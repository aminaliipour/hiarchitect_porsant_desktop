import sys
from database import Project,ProjectUser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, 
    QHBoxLayout, QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem, 
    QComboBox
)
from database import initialize_database, get_engine, User
from sqlalchemy.orm import sessionmaker

class CommissionCalculator(QWidget):
    def __init__(self):
        super().__init__()
        initialize_database()
        self.engine = get_engine()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('برنامه محاسبه پورسانت')
        self.setGeometry(100, 100, 600, 400)

        # تب‌ها
        self.tabs = QTabWidget()
        self.commission_tab = QWidget()
        self.users_tab = QWidget()
        self.projects_tab = QWidget()
        
        self.tabs.addTab(self.commission_tab, "محاسبه پورسانت")
        self.tabs.addTab(self.users_tab, "مدیریت کاربران")
        self.tabs.addTab(self.projects_tab, "مدیریت پروژه‌ها")
        
        # تنظیمات تب محاسبه پورسانت
        self.init_commission_tab()

        # تنظیمات تب مدیریت کاربران
        self.init_users_tab()

        # تنظیمات تب مدیریت پروژه‌ها
        self.init_projects_tab()

        # چیدمان اصلی
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    ## بخش محاسبه پورسانت
    def init_commission_tab(self):
        self.label_sales = QLabel('میزان فروش:')
        self.input_sales = QLineEdit()

        self.label_percentage = QLabel('درصد پورسانت:')
        self.input_percentage = QLineEdit()

        self.calculate_button = QPushButton('محاسبه')
        self.calculate_button.clicked.connect(self.calculate_commission)

        self.result_label = QLabel('پورسانت: 0')

        layout = QVBoxLayout()

        sales_layout = QHBoxLayout()
        sales_layout.addWidget(self.label_sales)
        sales_layout.addWidget(self.input_sales)

        percentage_layout = QHBoxLayout()
        percentage_layout.addWidget(self.label_percentage)
        percentage_layout.addWidget(self.input_percentage)

        layout.addLayout(sales_layout)
        layout.addLayout(percentage_layout)
        layout.addWidget(self.calculate_button)
        layout.addWidget(self.result_label)

        # افزودن استایل
        self.commission_tab.setLayout(layout)

    def calculate_commission(self):
        try:
            sales = float(self.input_sales.text())
            percentage = float(self.input_percentage.text())
            commission = sales * (percentage / 100)
            self.result_label.setText(f'پورسانت: {commission}')
        except ValueError:
            QMessageBox.warning(self, 'خطا', 'لطفاً اعداد معتبر وارد کنید.')

    ## بخش مدیریت کاربران
    def init_users_tab(self):
        layout = QVBoxLayout()

        # فرم افزودن کاربر
        form_layout = QHBoxLayout()
        self.user_name_input = QLineEdit()
        self.user_name_input.setPlaceholderText("نام کاربر")
        self.user_role_input = QLineEdit()
        self.user_role_input.setPlaceholderText("سمت کاربر")
        self.add_user_button = QPushButton("افزودن کاربر")
        self.add_user_button.clicked.connect(self.add_user)

        form_layout.addWidget(self.user_name_input)
        form_layout.addWidget(self.user_role_input)
        form_layout.addWidget(self.add_user_button)

        layout.addLayout(form_layout)

        # جدول نمایش کاربران
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["شناسه", "نام", "سمت"])
        self.load_users()

        layout.addWidget(self.users_table)

        self.users_tab.setLayout(layout)

    def add_user(self):
        name = self.user_name_input.text().strip()
        role = self.user_role_input.text().strip()
        if name and role:
            new_user = User(name=name, role=role)
            self.session.add(new_user)
            self.session.commit()
            QMessageBox.information(self, 'موفقیت', 'کاربر افزوده شد.')
            self.user_name_input.clear()
            self.user_role_input.clear()
            self.load_users()
        else:
            QMessageBox.warning(self, 'خطا', 'لطفاً تمامی فیلدها را پر کنید.')

    def load_users(self):
        self.users_table.setRowCount(0)
        users = self.session.query(User).all()
        for user in users:
            row_position = self.users_table.rowCount()
            self.users_table.insertRow(row_position)
            self.users_table.setItem(row_position, 0, QTableWidgetItem(str(user.id)))
            self.users_table.setItem(row_position, 1, QTableWidgetItem(user.name))
            self.users_table.setItem(row_position, 2, QTableWidgetItem(user.role))

    ## بخش مدیریت پروژه‌ها
    def init_projects_tab(self):
        layout = QVBoxLayout()

        # فرم افزودن پروژه
        form_layout = QHBoxLayout()
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("نام پروژه")
        self.project_description_input = QLineEdit()
        self.project_description_input.setPlaceholderText("توضیحات پروژه")
        self.add_project_button = QPushButton("افزودن پروژه")
        self.add_project_button.clicked.connect(self.add_project)

        form_layout.addWidget(self.project_name_input)
        form_layout.addWidget(self.project_description_input)
        form_layout.addWidget(self.add_project_button)

        layout.addLayout(form_layout)

        # جدول نمایش پروژه‌ها
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(3)
        self.projects_table.setHorizontalHeaderLabels(["شناسه", "نام", "توضیحات"])
        self.load_projects()

        layout.addWidget(self.projects_table)

        # فرم انتخاب کاربران برای پروژه
        assign_layout = QHBoxLayout()
        self.select_project_combo = QComboBox()
        self.load_project_combo()
        self.select_user_combo = QComboBox()
        self.load_user_combo()
        self.assign_user_button = QPushButton("انتخاب کاربر برای پروژه")
        self.assign_user_button.clicked.connect(self.assign_user_to_project)

        assign_layout.addWidget(QLabel("انتخاب پروژه:"))
        assign_layout.addWidget(self.select_project_combo)
        assign_layout.addWidget(QLabel("انتخاب کاربر:"))
        assign_layout.addWidget(self.select_user_combo)
        assign_layout.addWidget(self.assign_user_button)

        layout.addLayout(assign_layout)

        # جدول نمایش ارتباط پروژه و کاربران
        self.project_users_table = QTableWidget()
        self.project_users_table.setColumnCount(3)
        self.project_users_table.setHorizontalHeaderLabels(["شناسه ارتباط", "پروژه", "کاربر"])
        self.load_project_users()

        layout.addWidget(self.project_users_table)

        self.projects_tab.setLayout(layout)

    def add_project(self):
        name = self.project_name_input.text().strip()
        description = self.project_description_input.text().strip()
        if name:
            new_project = Project(name=name, description=description)
            self.session.add(new_project)
            self.session.commit()
            QMessageBox.information(self, 'موفقیت', 'پروژه افزوده شد.')
            self.project_name_input.clear()
            self.project_description_input.clear()
            self.load_projects()
            self.load_project_combo()
        else:
            QMessageBox.warning(self, 'خطا', 'نام پروژه الزامی است.')

    def load_projects(self):
        self.projects_table.setRowCount(0)
        projects = self.session.query(Project).all()
        for project in projects:
            row_position = self.projects_table.rowCount()
            self.projects_table.insertRow(row_position)
            self.projects_table.setItem(row_position, 0, QTableWidgetItem(str(project.id)))
            self.projects_table.setItem(row_position, 1, QTableWidgetItem(project.name))
            self.projects_table.setItem(row_position, 2, QTableWidgetItem(project.description if project.description else ""))
    
    def load_project_combo(self):
        self.select_project_combo.clear()
        projects = self.session.query(Project).all()
        for project in projects:
            self.select_project_combo.addItem(f"{project.id} - {project.name}", project.id)

    def load_user_combo(self):
        self.select_user_combo.clear()
        users = self.session.query(User).all()
        for user in users:
            self.select_user_combo.addItem(f"{user.id} - {user.name}", user.id)

    def load_user_combo(self):
        self.select_user_combo.clear()
        users = self.session.query(User).all()
        for user in users:
            self.select_user_combo.addItem(f"{user.id} - {user.name}", user.id)

    def assign_user_to_project(self):
        project_index = self.select_project_combo.currentIndex()
        project_id = self.select_project_combo.itemData(project_index)
        user_index = self.select_user_combo.currentIndex()
        user_id = self.select_user_combo.itemData(user_index)
        
        if project_id and user_id:
            # بررسی وجود قبلی ارتباط
            existing = self.session.query(ProjectUser).filter_by(project_id=project_id, user_id=user_id).first()
            if existing:
                QMessageBox.warning(self, 'خطا', 'این کاربر قبلاً به این پروژه اختصاص داده شده است.')
                return
            new_assignment = ProjectUser(project_id=project_id, user_id=user_id)
            self.session.add(new_assignment)
            self.session.commit()
            QMessageBox.information(self, 'موفقیت', 'کاربر به پروژه اختصاص داده شد.')
            self.load_project_users()
        else:
            QMessageBox.warning(self, 'خطا', 'انتخاب پروژه و کاربر الزامی است.')

    def load_project_users(self):
        self.project_users_table.setRowCount(0)
        assignments = self.session.query(ProjectUser).all()
        for assignment in assignments:
            project = self.session.query(Project).filter_by(id=assignment.project_id).first()
            user = self.session.query(User).filter_by(id=assignment.user_id).first()
            row_position = self.project_users_table.rowCount()
            self.project_users_table.insertRow(row_position)
            self.project_users_table.setItem(row_position, 0, QTableWidgetItem(str(assignment.id)))
            self.project_users_table.setItem(row_position, 1, QTableWidgetItem(project.name if project else ""))
            self.project_users_table.setItem(row_position, 2, QTableWidgetItem(user.name if user else ""))

    ## پایان مدیریت پروژه‌ها

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CommissionCalculator()
    window.show()
    sys.exit(app.exec_())
