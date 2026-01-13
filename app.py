from flask import Flask, render_template, url_for, request, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os 


# ====== Создание приложения Flask ======
app = Flask(__name__)

app.config['SECRET_KEY'] = '}WW?9vP]]&YK!,D2.CK~m+az3VipL2V%8?o\$NO>'
# ====== Настройки базы данных ======
# Используем SQLite файл blog.db
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # отключаем лишние уведомления


UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)  # создаём объект базы данных
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ====== Модели (таблицы базы данных) ======


class Article(db.Model):
    # Таблица статей
    id = db.Column(db.Integer, primary_key = True)  # уникальный ID
    title = db.Column(db.String(100), nullable = False)  # заголовок
    intro = db.Column(db.String(300), nullable = False)  # краткое описание
    text = db.Column(db.Text, nullable = False)  # основной текст статьи
    date = db.Column(db.DateTime, default = datetime.utcnow)  # дата создания (по умолчанию сейчас)
    
    def __repr__(self):
        # как объект отображается в консоли для отладки
        return "<Article %r>" % self.id
  
    
class Item(db.Model):
    # Таблица товаров
    id = db.Column(db.Integer, primary_key = True)  # уникальный ID
    title = db.Column(db.String(100), nullable = False)  # название товара
    price = db.Column(db.Integer, nullable = False)  # цена товара
    isActive = db.Column(db.Boolean, default = True)  # флаг активности товара
    text = db.Column(db.Text, nullable = False)  # описание товара
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable = False)
    images = db.relationship('ItemImage', backref='item', lazy=True, cascade="all, delete")
    views = db.Column(db.Integer, default = 0)
    artist = db.Column(db.String(100), nullable = False)
    genre = db.Column(db.String(50), nullable = False)
    release_year = db.Column(db.Integer, nullable = False)
    
    
    
    def __repr__(self):
        return "<Item %r>" % self.id
   
    
class ItemImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable = False)
    filename = db.Column(db.String(100), nullable=False)
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique = True, nullable = False)
    password_hash = db.Column(db.String(200), nullable = False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
       self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
# ====== Роуты (URL-адреса сайта) ======

@app.route('/')
@app.route('/home')
def index():
    popular_items = Item.query.order_by(Item.views.desc()).limit(4).all()
    # Главная страница
    return render_template("index.html", popular_items = popular_items)  # отображаем index.html

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        if User.query.filter_by(username=username).first():
            return "Пользователь с таким именем уже существует"
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()   
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.check_password(request.form["password"]):
            login_user(user)
            return redirect(url_for('index'))
        return "неверный логин или пароль"
    return render_template('login.html')
            
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/about')
def about():
    # Страница "О нас"
    return render_template("about.html")


@app.route('/posts')
def posts():
    # Страница со списком всех статей
    articles = Article.query.order_by(Article.date.desc()).all()  # достаем все статьи из базы, сортируем по дате (сначала новые)
    return render_template("posts.html", articles=articles)  # передаём список статей в шаблон


@app.route('/cat')
def cat():
    # 1. Получаем параметры из URL
    sort = request.args.get("sort")
    filter_active = request.args.get("active")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    
    # Получаем списки выбранных значений (checkbox)
    # Используем названия 'artist', 'genre', 'year' как в атрибуте name="..." в HTML
    artists_selected = request.args.getlist("artist")
    genres_selected = request.args.getlist("genre")
    years_selected = request.args.getlist("year")
    
    # 2. Собираем ВСЕ уникальные значения для выпадающих списков
    # Это нужно, чтобы в меню было из чего выбирать
    artists_db = db.session.query(Item.artist).distinct().order_by(Item.artist).all()
    genres_db = db.session.query(Item.genre).distinct().order_by(Item.genre).all()
    years_db = db.session.query(Item.release_year).distinct().order_by(Item.release_year.desc()).all()
    
    # Распаковываем кортежи в простые списки
    all_artists = [a[0] for a in artists_db if a[0]]
    all_genres = [g[0] for g in genres_db if g[0]]
    all_years = [y[0] for y in years_db if y[0]]
    
    page = request.args.get('page', 1, type=int)
    per_page = 40
    
    # 3. Начинаем строить запрос к базе
    query = Item.query
    
    # 4. ФИЛЬТРАЦИЯ
    if filter_active == '1':
        query = query.filter(Item.isActive == True)
        
    if min_price:
        query = query.filter(Item.price >= int(min_price))
    if max_price:
        query = query.filter(Item.price <= int(max_price))
        
    # Множественный выбор (используем .in_)
    if artists_selected:
        query = query.filter(Item.artist.in_(artists_selected))
    
    if genres_selected:
        query = query.filter(Item.genre.in_(genres_selected))
        
    if years_selected:
        # Конвертируем список строк из URL в числа для базы данных
        years_as_ints = [int(y) for y in years_selected]
        query = query.filter(Item.release_year.in_(years_as_ints))
    
    # 5. СОРТИРОВКА
    if sort == "price_asc":
        query = query.order_by(Item.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Item.price.desc())
    elif sort == "popular":
        query = query.order_by(Item.views.desc())
    elif sort == "old":
        query = query.order_by(Item.created_at.asc())
    else:
        query = query.order_by(Item.created_at.desc())
        
    pagination = query.paginate(page = page, per_page = per_page, error_out = False)
    items = pagination.items
    # 6. Передаем всё в шаблон
    return render_template(
        "cat.html", 
        items=items, 
        sort=sort, 
        filter_active=filter_active,
        artists=all_artists,              # Все доступные артисты
        genres=all_genres,                # Все доступные жанры
        years=all_years,                  # Все доступные годы
        artists_selected=artists_selected, # Выбранные пользователем
        genres_selected=genres_selected, 
        years_selected=years_selected,
        pagination=pagination
    )
@app.route('/posts/<int:id>')
def post_detail(id):
    # Страница отдельной статьи
    article = Article.query.get(id)  # достаем статью по ID
    return render_template("post_detail.html", article=article)

 
@app.route('/cat/<int:id>')
def item_detail(id):
    # Страница отдельного товара
    item = Item.query.get_or_404(id)  # достаем товар по ID
    item.views = (item.views or 0) + 1
    db.session.commit()
    return render_template("item_detail.html", item=item)

# ====== CRUD для статей и товаров======


@app.route('/posts/<int:id>/delete')
@login_required
@admin_required
def post_delete(id):
    # Удаление статьи
    article = Article.query.get_or_404(id)  # достаем статью по ID или выдаём 404
    try:
                
        db.session.delete(article)  # удаляем из базы
        db.session.commit()  # подтверждаем изменения
        return redirect("/posts")  # возвращаемся на список статей
    except:
        return "Произошла ошибка" 
 
    
@app.route('/cat/<int:id>/delete')
@login_required
@admin_required
def item_delete(id):
    # Удаление товара
    item = Item.query.get_or_404(id)  # достаем товар по ID или выдаём 404
    try:
        
        # Удаляем файлы изображений с диска
        for img in item.images:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
            if os.path.exists(img_path):
                os.remove(img_path)
        
        
        db.session.delete(item)  # удаляем из базы
        db.session.commit()  # подтверждаем изменения
        return redirect("/cat")  # возвращаемся в список товаров 
    except:
        return "Произошла ошибка"    


@app.route('/posts/<int:id>/update', methods=['POST','GET'])
@login_required
@admin_required
def post_update(id):
    # Редактирование статьи
    article = Article.query.get(id)  # достаем статью по ID
    if request.method == "POST":
        # Если форма отправлена методом POST — обновляем данные
        article.title = request.form["title"]
        article.intro = request.form["intro"]
        article.text = request.form["text"]
        
        try:
            db.session.commit()  # сохраняем изменения
            return redirect("/posts")
        except:
            return "Возникла ошибка"
    else:
        # Если метод GET — отображаем форму с текущими данными
        return render_template("post_update.html", article=article)





@app.route('/cat/<int:id>/update', methods=['POST','GET'])
@login_required
@admin_required
def item_update(id):
    # Редактирование товара
    item = Item.query.get_or_404(id)  # достаем товар по ID
    if request.method == "POST":
        # Если форма отправлена методом POST — обновляем данные
        item.title = request.form["title"]
        item.price = request.form["price"]
        item.text = request.form["text"]
        item.artist = request.form["artist"]
        item.genre = request.form["genre"]
        item.release_year = request.form["release_year"]
        
        files = request.files.getlist('images')
        
        try:
            
            if files and files[0].filename != "":
                for img in item.images:
                    img_path = os.path.join(app.config["UPLOAD_FOLDER"],img.filename)
                    if os.path.exists(img_path):
                        os.remove(img_path)
                    db.session.delete(img)
                for file in files:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))
                    new_img = ItemImage(item_id=item.id,filename=filename)
                    db.session.add(new_img)
                    
                    
            db.session.commit()  # сохраняем изменения
            return redirect("/cat")
        except:
            return "Возникла ошибка"
    else:
        # Если метод GET — отображаем форму с текущими данными
        return render_template("item_update.html", item=item)


@app.route('/create-article', methods=['POST','GET'])
@login_required
@admin_required


def create_article():
    # Создание новой статьи
    if request.method == "POST":
        # Получаем данные из формы
        title = request.form["title"]
        intro = request.form["intro"]
        text = request.form["text"]
        
        article = Article(title=title,intro=intro,text=text)  # создаем объект статьи
        
        try:
            db.session.add(article)  # добавляем в базу
            db.session.commit()  # сохраняем изменения
            return redirect("/posts")  # перенаправляем на список статей
        except:
            return "Возникла ошибка"
    else:
        # Если метод GET — отображаем форму создания
        return render_template("create-article.html")
   
    
@app.route('/create-item', methods=['POST','GET'])
@login_required
@admin_required
def create_item():
    # Создание нового товара
    if request.method == "POST":
        # Получаем данные из формы
        title = request.form["title"]
        price = request.form["price"]
        text = request.form["text"]
        artist = request.form["artist"]
        genre = request.form["genre"]
        release_year = request.form["release_year"]
        
        item = Item(title=title,price=price,text=text, artist = artist, genre=genre,release_year=release_year)  # создаём объект товара
        
        try:
            db.session.add(item)  # добавляем в базу
            db.session.commit()  # сохраняем изменения
            
            
            files = request.files.getlist('images')
            for file in files:
                if file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    img = ItemImage(item_id=item.id, filename=filename)
                    db.session.add(img)
            db.session.commit()
            
            
            return redirect("/cat")  # перенаправляем на каталог
        except:
            return "Возникла ошибка"
    else:
        # Если метод GET — отображаем форму создания
        return render_template("create-item.html")



# ====== Запуск приложения ======
if __name__ == "__main__":
    app.run(debug=True)  # запускаем сервер Flask в режиме отладки
