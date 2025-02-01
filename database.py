from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# پایه مدل‌های SQLAlchemy
Base = declarative_base()

# مدل User: شامل id، name و role
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    
    # ایجاد رابطه با جدول میانی ProjectUser برای دسترسی به پروژه‌های مرتبط با کاربر
    projects = relationship('ProjectUser', back_populates='user')

# مدل Project: شامل id، name، description و net_profit
class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    net_profit = Column(Float, default=0.0)  # ذخیره سود واقعی پروژه
    
    # ایجاد رابطه با جدول میانی ProjectUser برای دسترسی به کاربران مرتبط با پروژه
    users = relationship('ProjectUser', back_populates='project')

# مدل ProjectUser: جدول میانی برای ارتباط بین پروژه‌ها و کاربران
class ProjectUser(Base):
    __tablename__ = 'project_users'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    user_id = Column(Integer, ForeignKey('users.id'))

    # ارتباط معکوس برای اتصال به مدل‌های Project و User
    project = relationship('Project', back_populates='users')
    user = relationship('User', back_populates='projects')

# تابع get_engine برای ایجاد ارتباط با پایگاه داده
def get_engine():
    return create_engine('sqlite:///database.db')

# تابع initialize_database برای ایجاد جدول‌های پایگاه داده
def initialize_database():
    engine = get_engine()
    Base.metadata.create_all(engine)

# اجرا در صورت اجرای مستقیم فایل به صورت اسکریپت
if __name__ == '__main__':
    initialize_database()
    print("پایگاه داده با استفاده از SQLAlchemy ایجاد شد.")
