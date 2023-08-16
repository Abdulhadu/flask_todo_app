from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager , UserMixin , login_required ,login_user, logout_user,current_user
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy import or_
from enum import Enum
from flask import jsonify
from flask.views import View
from sqlalchemy import text
from sqlalchemy import Sequence

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config['SECRET_KEY']='619619'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)

PER_PAGE = 5 

class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200),  nullable=False)
    category = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    user_email = db.Column(db.String(200), nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False,
        default=datetime.utcnow)


    def __repr__(self)-> str:
        return f"{self.sno} - {self.title}"
    
class SubTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.sno'), nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)

class UserRole(Enum):
    STAFF = "staff"
    ADMIN = "admin"
    NORMAL_USER = "normal user"
    
    
class UserType(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    User = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.NORMAL_USER)
    
@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    
    user_id = data.get('user_id')
    role=UserRole.NORMAL_USER.value

    # try:
    #       db.execute(
    #                 "INSERT INTO ser_type (User, role) VALUES (?, ?)",
    #                 (user_id , role),
    #             )
    #       db.commit()
    # except db.IntegrityError:
    #     error = f"User is not registered."
    # else:
    #     return "User type created successfully."
    
    user_id = data.get('user_id')
    role = data.get('role', UserRole.NORMAL_USER.value)

    user_type = UserType(User=user_id, role=UserRole(role))
    db.session.add(user_type)
    db.session.commit()
    

    
@app.route('/get_all_users', methods=['GET'])
def get_all_users():
    sql = text("SELECT user.id, user.email, user_type.role FROM user JOIN User_type ON user.id = user_type.User")
    
    with db.engine.connect() as connection:
        result = connection.execute(sql)
    
        user_list = []
        for row in result:
            user_data = {
                "id": row.id,
                "email": row.email,
                "role": row.role
            }
            user_list.append(user_data)

    return jsonify(user_list)

     
    
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
    if user and user.password == password:  # Plain text password check
        login_user(user)
        flash("You have been logged in successfully!", "success")
        if user.is_admin:
            return redirect('/admin')
        else:
            return redirect('/')
    else:
        flash("Invalid email or password. Please try again.", "danger")
        return redirect('/login') 
        

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

@app.route('/admin', methods=['GET'])
@login_required
def admin_panel():
    if current_user.is_admin:
        total_users = User.query.count()
        users_with_todo_count = []

        for user in User.query.all():
            todo_count = Todo.query.filter_by(user_email=user.email).count()
            users_with_todo_count.append({'user': user, 'todo_count': todo_count})

        return render_template('admin.html', total_users=total_users, users_with_todo_count=users_with_todo_count)
    else:
        return "You do not have permission to access this page."
    
    
@app.route('/create_admin', methods=['GET'])
def create_admin():
    # Create an admin user if it doesn't already exist
    admin_user = User.query.filter_by(email='admin@example.com').first()
    if not admin_user:
        admin_user = User(email='admin@example.com', password='adminpassword', is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        return "Admin user created successfully."
    else:
        return "Admin user already exists."
    

@app.route("/", methods=['GET', 'POST'])
def hello_world():
    allTodo = []  # Initialize the variable outside of the if block
    total_pages = 0  # Initialize total_pages to 0

    if request.method == "POST":
        Title = request.form['title']
        Category = request.form['category']
        Desc = request.form['desc']
        print("user is", current_user.email)

        if current_user.is_authenticated:
            email = current_user.email
            todo = Todo(title=Title, category=Category, desc=Desc, user_email=email)
            db.session.add(todo)
            db.session.commit()
            flash("Todo Added Successfully..!")

    page = request.args.get('page', 1, type=int)

    if current_user.is_authenticated:
        user_email = current_user.email
        allTodo, total_pages = get_paginated_todos(page, user_email)
        
        return render_template('index.html', allTodo=allTodo, current_user=current_user, total_pages=total_pages)
    else:
        return redirect('/login')



def get_paginated_todos(page, user_email, search=None):
    per_page = 5
    query = Todo.query.filter_by(user_email=user_email).order_by(Todo.pub_date.desc())

    if search:
        query = query.filter(
            or_(
                Todo.title.ilike(f'%{search}%'),
                Todo.desc.ilike(f'%{search}%'),
                Todo.category.ilike(f'%{search}%')
            )
        )

    allTodo = query.paginate(page=page, per_page=per_page)
    total_pages = allTodo.pages
    start_index = (page - 1) * per_page + 1

    for index, todo in enumerate(allTodo.items, start=start_index):
        todo.index = index
        todo.subtasks_count = SubTask.query.filter_by(todo_id=todo.sno).count() 

    return allTodo.items, total_pages


@app.route("/search", methods=['GET', 'POST'])
def search():
    per_page = 5
    page = request.args.get('page', 1, type=int)
    search_query = request.form.get('search') if request.method == 'POST' else None

    if current_user.is_authenticated:
        user_email = current_user.email
        allTodo, total_pages = get_paginated_todos(page, user_email, search=search_query)

        return render_template('index.html', allTodo=allTodo, current_user=current_user, total_pages=total_pages)
    else:
        return redirect('/login')

# I am using the class based views in the subtask and remove two separate End points The class based Views provide the functionality to create more then onwe function views and then app.add_rule_url
class TaskView(View):
    methods = ['GET', 'POST']

    def dispatch_request(self, sno):
        if request.method == "POST":
            sub_Title = request.form['title']
            sub_Desc = request.form['desc']
            if current_user.is_authenticated:
                sub_Task = SubTask(title=sub_Title, desc=sub_Desc, todo_id=sno)
                db.session.add(sub_Task)
                db.session.commit()
                flash("Task added Successfully..!")
                return redirect(f'/task/{sno}')
            else:
                flash("Dont have permission. Please Login first to add tasks")
                return redirect('/login')
        else:
            todo = Todo.query.get_or_404(sno)
            alltask = SubTask.query.filter_by(todo_id=sno).all()
            return render_template('subtask.html', todo=todo, alltask=alltask, sno=sno)

app.add_url_rule('/task/<int:sno>', view_func=TaskView.as_view('subtask.html'))



            
@app.route("/update/<int:sno>",  methods=['GET','POS'])
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
     flash("Successfully Updated..!")
     return render_template('update.html', updateTodo = updateTodo)

@app.route('/delete/<int:sno>')
def delete(sno):
    deleteTodo = Todo.query.filter_by(sno = sno).first()
    db.session.delete(deleteTodo)
    db.session.commit()
    flash("Deleted Successfully..!")
    return redirect("/")


@app.route('/deleteSubtask/<int:id>')
def deletesubtask(id):
    deleteSubtask = SubTask.query.get(id)
    if deleteSubtask:
        sno = deleteSubtask.todo_id
        db.session.delete(deleteSubtask)
        db.session.commit()
    flash("Deleted Successfully..!")
    return redirect(f"/displaytask/{sno}")
    

if __name__ == "__main__":
    app.run(debug=True)