from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os 


# ====== Создание приложения Flask ======
app = Flask(__name__)


# ====== Настройки базы данных ======
# Используем SQLite файл blog.db
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # отключаем лишние уведомления


UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)  # создаём объект базы данных


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
    images = db.relationship('ItemImage', backref='item', lazy=True, cascade="all, delete")
    
    def __repr__(self):
        return "<Item %r>" % self.id
   
    
class ItemImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable = False)
    filename = db.Column(db.String(100), nullable=False)

# ====== Роуты (URL-адреса сайта) ======

@app.route('/')
@app.route('/home')
def index():
    # Главная страница
    return render_template("index.html")  # отображаем index.html


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
    # Страница каталога товаров
    items = Item.query.order_by(Item.price).all()  # достаем все товары, сортируем по цене
    return render_template("cat.html", items=items)  # передаем товары в шаблон


@app.route('/posts/<int:id>')
def post_detail(id):
    # Страница отдельной статьи
    article = Article.query.get(id)  # достаем статью по ID
    return render_template("post_detail.html", article=article)

 
@app.route('/cat/<int:id>')
def item_detail(id):
    # Страница отдельного товара
    item = Item.query.get(id)  # достаем товар по ID
    return render_template("item_detail.html", item=item)

# ====== CRUD для статей и товаров======


@app.route('/posts/<int:id>/delete')
def post_delete(id):
    # Удаление статьи
    article = Article.query.get_or_404(id)  # достаем статью по ID или выдаём 404
    try:
        
         # Удаляем файлы изображений с диска
        for img in item.images:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
            if os.path.exists(img_path):
                os.remove(img_path)
                
        db.session.delete(article)  # удаляем из базы
        db.session.commit()  # подтверждаем изменения
        return redirect("/posts")  # возвращаемся на список статей
    except:
        return "Произошла ошибка" 
 
    
@app.route('/cat/<int:id>/delete')
def item_delete(id):
    # Удаление товара
    item = Item.query.get_or_404(id)  # достаем товар по ID или выдаём 404
    try:
        db.session.delete(item)  # удаляем из базы
        db.session.commit()  # подтверждаем изменения
        return redirect("/cat")  # возвращаемся в список товаров 
    except:
        return "Произошла ошибка"    


@app.route('/posts/<int:id>/update', methods=['POST','GET'])
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
def item_update(id):
    # Редактирование товара
    item = Item.query.get(id)  # достаем товар по ID
    if request.method == "POST":
        # Если форма отправлена методом POST — обновляем данные
        item.title = request.form["title"]
        item.price = request.form["price"]
        item.text = request.form["text"]
        
        try:
            db.session.commit()  # сохраняем изменения
            return redirect("/cat")
        except:
            return "Возникла ошибка"
    else:
        # Если метод GET — отображаем форму с текущими данными
        return render_template("item_update.html", item=item)


@app.route('/create-article', methods=['POST','GET'])


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
def create_item():
    # Создание нового товара
    if request.method == "POST":
        # Получаем данные из формы
        title = request.form["title"]
        price = request.form["price"]
        text = request.form["text"]
        
        item = Item(title=title,price=price,text=text)  # создаём объект товара
        
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
