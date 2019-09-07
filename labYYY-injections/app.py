# Imports
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from flask_graphql import GraphQLView

basedir = os.path.abspath(os.path.dirname(__file__))

# app initialization
try:
	app = Flask(__name__, static_url_path='/static', static_folder='static')
	app.debug = True
except GraphQLError as gqle:
	raise gqle

# Configs

## Configuring the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' +    os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# Modules

## Declaring the database
db = SQLAlchemy(app)


# Models
#     1 User -> N Post 
#
#	  1 Post -> 1 User


class User(db.Model):
    __tablename__ = 'users'
    uuid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), index=True, unique=True)
    posts = db.relationship('Post', backref='author') ## HERE is the problem, that enables to create recursive queries
    
    def __repr__(self):
        return '<User %r>' % self.username

class Post(db.Model):
    __tablename__ = 'posts'
    uuid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), index=True)
    body = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.uuid'))
    #author = db.relationship('User', backref='post')
    
    def __repr__(self):
        return '<Post %r>' % self.title

# Schema Objects
class PostObject(SQLAlchemyObjectType):
    class Meta:
        model = Post
        interfaces = (graphene.relay.Node, )

class UserObject(SQLAlchemyObjectType):
   class Meta:
       model = User
       interfaces = (graphene.relay.Node, )

class PostAttribute:
	title = graphene.String(description="Title of the post")
	body = graphene.String(description="Description")
	author_id = graphene.Int()

class CreatePostInput(graphene.InputObjectType, PostAttribute):
    """Arguments to create a post."""
    pass

class CreatePost(graphene.Mutation):
    """Mutation to create a person."""
    post = graphene.Field(lambda: PostObject, description="Post created by this mutation.")
    class Arguments:
        input = CreatePostInput(required=True)

    def mutate(self, info, input):
        post = Post(**input)
        db.session.add(post)
        db.session.commit()
        return CreatePost(post=post)

class Query(graphene.ObjectType):
    """query the status of a server after ping"""
    is_sql_up = graphene.String(ip=graphene.String(required=True))

    @staticmethod
    def resolve_is_sql_up(self,info,ip):
        #exec ping command against the IP; return status code
        host,port = ip.split(':')
        res = os.system('nc -w 3 ' + host + " " + port)
        return res 

    """query User information"""
    get_user = graphene.Field(UserObject, username=graphene.String(required=True))

    @staticmethod
    def resolve_get_user(self,info,username):
        #sql query
        res = db.session.execute("select * form users where username ='" + username + "';")
        return res

#4
class Mutation(graphene.ObjectType):
    create_post = CreatePost.Field()


schema = graphene.Schema(query=Query,mutation=Mutation)


# Routes
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True # for having the GraphiQL interface
    )
)

@app.route('/')
def index():
    #Implement logic to retrieve posts
    return render_template("index.html" )

@app.route('/admin')
def admin():
    #Implement logic to retrieve posts
    return render_template("admin.html" )



if __name__ == '__main__':
     app.run('0.0.0.0')