from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity
)

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/ocrolusdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '....'  # You can change this secret key

db = SQLAlchemy(app)
jwt = JWTManager(app)

# MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# ROUTES
@app.route('/')
def home():
    return "Article app is running!"


#Post method for registration username and password

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data.get('username') or not data.get('password'):
        return jsonify(message="Username and password required"), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify(message="Username already exists"), 400

    user = User(username=data['username'], password=data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify(message="Registered successfully")

#Post method for login with credentials

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify(message="Username and password required"), 400

    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify(message="Invalid credentials"), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(token=token)

@app.route('/articles', methods=['POST'])
@jwt_required()
def create_article():
    user_id = int(get_jwt_identity())
    data = request.json

    if not data.get("title") or not data.get("content"):
        return jsonify(message="Title and content required"), 400

    article = Article(title=data["title"], content=data["content"], author_id=user_id)
    db.session.add(article)
    db.session.commit()
    return jsonify(message="Article created")

#Get method with all articles list 

@app.route('/articles', methods=['GET'])
@jwt_required()
def list_articles():
    user_id = int(get_jwt_identity())
    articles = Article.query.filter_by(author_id=user_id).all()
    return jsonify([{"id": a.id, "title": a.title} for a in articles])


#Get method with id/title

@app.route('/article/<param>', methods=['GET'])
@jwt_required()
def view_article_by_param(param):
    user_id = int(get_jwt_identity())
    article = None

    if param.isdigit():
        article = Article.query.filter_by(id=int(param), author_id=user_id).first()
    else:
        article = Article.query.filter_by(title=param, author_id=user_id).first()

    if not article:
        return jsonify(message="Article not found"), 404

    return jsonify({
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "author_id": article.author_id

    })

#Put method

@app.route('/articles/<int:id>', methods=['PUT'])
@jwt_required()
def update_article(id):
    user_id = int(get_jwt_identity())
    article = Article.query.get_or_404(id)

    if article.author_id != user_id:
        return jsonify(message="Access denied"), 403

    data = request.json
    article.title = data.get('title', article.title)
    article.content = data.get('content', article.content)

    db.session.commit()
    return jsonify(message="Article updated")

#Patch method

@app.route('/articles/<int:id>', methods=['PATCH'])
@jwt_required()
def patch_article(id):
    user_id = int(get_jwt_identity())
    article = Article.query.get_or_404(id)

    if article.author_id != user_id:
        return jsonify(message="Access denied"), 403

    data = request.json
    if 'title' in data:
        article.title = data['title']
    if 'content' in data:
        article.content = data['content']

    db.session.commit()
    return jsonify(message="Article partially updated")

#Delete method

@app.route('/articles/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_article(id):
    user_id = int(get_jwt_identity())
    article = Article.query.get_or_404(id)

    if article.author_id != user_id:
        return jsonify(message="Access denied"), 403

    db.session.delete(article)
    db.session.commit()
    return jsonify(message="Article deleted")

# Initialize DB and run app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
