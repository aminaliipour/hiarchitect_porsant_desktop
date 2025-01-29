from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    
    projects = relationship('Project', secondary='project_users', back_populates='users')

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    
    users = relationship('User', secondary='project_users', back_populates='projects')

class ProjectUser(Base):
    __tablename__ = 'project_users'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    user_id = Column(Integer, ForeignKey('users.id'))

def get_engine():
    return create_engine('sqlite:///database.db')

def initialize_database():
    engine = get_engine()
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    initialize_database()
    print("پایگاه داده با استفاده از SQLAlchemy ایجاد شد.")
