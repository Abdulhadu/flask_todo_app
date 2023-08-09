from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager , UserMixin , login_required ,login_user, logout_user,current_user
from flask_paginate import Pagination, get_page_args
from flask_migrate import Migrate
from datetime import datetime



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config['SECRET_KEY']='619619'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

PER_PAGE = 5 

class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200),  nullable=False)
    category = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False,
        default=datetime.utcnow)
    
    def __repr__(self)-> str:
        return f"{self.sno} - {self.title}"
    
    
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))
    
@login_manager.user_loader
def get(id):
    return User.query.get(id)

@app.route('/login',methods=['GET'])
def get_login():
    return render_template('login.html')

@app.route('/signup',methods=['GET'])
def get_signup():
    return render_template('signup.html')


@app.route('/login',methods=['POST'])
def login_post():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email).first()
    login_user(user)
    return redirect('/')

@app.route('/signup',methods=['POST'])
def signup_post():
    email = request.form['email']
    password = request.form['password']
    cpassword = request.form['cpassword']
    if password == cpassword:
        user = User(email=email,password=password)
        db.session.add(user)
        db.session.commit()
        user = User.query.filter_by(email=email).first()
        login_user(user)
        return redirect('/')
    
    
@app.route('/logout',methods=['GET'])
def logout():
    logout_user()
    return redirect('/login')

@app.route('/account',methods=['GET'])
@login_required
def get_account():
    return render_template('account.html')
        
@app.route("/", methods=['GET','POST'])
def hello_world():
    if request.method=="POST":
        Title=request.form['title']
        Category=request.form['category']
        Desc=request.form['desc']
        todo =Todo(title = Title, category = Category, desc = Desc)
        db.session.add(todo)
        db.session.commit()
        
    page = request.args.get('page', 1, type=int)
    allTodo, total_pages = get_paginated_todos(page)
    return render_template('index.html', allTodo = allTodo, current_user=current_user, total_pages=total_pages)

def get_paginated_todos(page):
    per_page = 5  # Set the number of items per page
    allTodo = Todo.query.order_by(Todo.pub_date.desc()).paginate(page=page, per_page=per_page)
    total_pages = allTodo.pages
     # Calculate the starting index for the current page
    start_index = (page - 1) * per_page + 1

    # Calculate the index value for each item
    for index, todo in enumerate(allTodo.items, start=start_index):
        todo.index = index
    return allTodo.items, total_pages

@app.route("/update/<int:sno>",  methods=['GET','POST'])
def update(sno):
     if request.method=="POST":
        Title=request.form['title']
        Category=request.form['category']
        Desc=request.form['desc']
        updateTodo = Todo.query.filter_by(sno = sno).first()
        updateTodo.title=Title
        updateTodo.category=Category
        updateTodo.desc=Desc
        db.session.add(updateTodo)
        db.session.commit()
        return redirect("/")
    
     updateTodo = Todo.query.filter_by(sno = sno).first()   
     return render_template('update.html', updateTodo = updateTodo)

@app.route('/delete/<int:sno>')
def delete(sno):
    deleteTodo = Todo.query.filter_by(sno = sno).first()
    db.session.delete(deleteTodo)
    db.session.commit()
    return redirect("/")


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method== 'POST':
        title =  request.form.get('search')
        print ("title is",request.form.get('search'))
        search = "%{}%".format(title)
        allTodo = Todo.query.filter(Todo.title.ilike(search)).all() 
        return render_template('index.html', allTodo=allTodo)
    else:
        allTodo = Todo.query.all()
        return render_template('index.html', allTodo=allTodo)
        
    
if __name__ == "__main__":
    app.run(debug=True)