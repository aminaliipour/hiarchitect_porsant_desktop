import sys
from database import Project, ProjectUser, User, initialize_database, get_engine
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, 
    QHBoxLayout, QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem, 
    QComboBox, QDialog, QFormLayout, QInputDialog, QCheckBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt
from sqlalchemy.orm import sessionmaker

# در صورت نیاز؛ اگر در مدل Project ستونی برای ذخیره سود واقعی ندارید، می‌توانید آن را به صورت زیر اضافه کنید:
# مثلا:
# class Project(Base):
#    __tablename__ = 'projects'
#    id = Column(Integer, primary_key=True)
#    name = Column(String(250))
#    description = Column(String(500))
#    net_profit = Column(Float, default=0.0)
#
# توجه داشته باشید که در این نسخه ما فرض می‌کنیم ستون net_profit برای نمایش سود واقعی در پروژه موجود است.


################################################################################
# دیالوگ برای وارد کردن منابع مالی پروژه و اختصاص کاربران به پروژه
################################################################################
class FinanceDialog(QDialog):
    def __init__(self, parent, project_id, session):
        super().__init__(parent)
        self.session = session
        self.project_id = project_id
        self.setWindowTitle("افزودن منابع مالی و اختصاص کاربران")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.income_categories = {
            "سود از خرید": None,
            "سود از طراحی": None,
            "سود از همکاری با استادکاران و شرکای تجاری": None,
            "سود از درصد پیمانکاری": None,
            "سود از فروش": None,
            "سود از تبلیغات و ارجاع": None,
            "سود از مشاوره": None,
        }
        self.expense_categories = {
            "حقوق پرسنل": None,
            "هزینه‌های جاری دفتر (کرایه، آب، برق، گاز)": None,
            "هزینه افزایش کرایه و پول پیش": None,
            "تعمیرات، بازسازی و استهلاک": None,
            "ارتقای فضای کار": None,
            "ارتقای ابزار کار": None,
            "تبلیغات و تولید محتوا": None,
            "توسعه صفحات مجازی و سایت (طراحی سایت+CEO)": None,
            "هزینه‌های سیستم (میزیتو، تنخواه گردان و ...)": None,
            "هزینه‌های حسابداری": None,
            "هزینه اسناد کاغذی (پرینت، بنر، کارت، سربرگ، ست اداری و ...)": None,
            "نمایشگاه‌ها و ایونت‌ها": None,
            "پرداخت به ارجاع مشتری و پورسانت": None,
            "هزینه‌های دادرسی و کیفری": None,
        }
        self.user_checkboxes = []

        # ساخت فرم برای درآمدها
        self.layout.addWidget(QLabel("درآمدها:"))
        self.income_form = QFormLayout()
        self.income_inputs = {}
        for label in self.income_categories:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText("عدد مثبت (مثال: 10000)")
            self.income_inputs[label] = line_edit
            self.income_form.addRow(label, line_edit)
        self.layout.addLayout(self.income_form)

        # ساخت فرم برای هزینه‌ها
        self.layout.addWidget(QLabel("هزینه‌ها:"))
        self.expense_form = QFormLayout()
        self.expense_inputs = {}
        for label in self.expense_categories:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText("عدد مثبت (مثال: 8000)")
            self.expense_inputs[label] = line_edit
            self.expense_form.addRow(label, line_edit)
        self.layout.addLayout(self.expense_form)

        # اختصاص کاربران به پروژه:
        self.layout.addWidget(QLabel("اختصاص کاربران به پروژه:"))
        self.users_list = QListWidget()
        self.load_users()
        self.layout.addWidget(self.users_list)

        # دکمه‌ها
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("ذخیره")
        self.save_button.clicked.connect(self.save_finance)
        button_layout.addWidget(self.save_button)
        self.cancel_button = QPushButton("انصراف")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)

    def load_users(self):
        # بارگذاری کاربران از پایگاه داده
        users = self.session.query(User).all()
        for user in users:
            item = QListWidgetItem(f"{user.id} - {user.name}")
            item.setData(Qt.UserRole, user.id)
            # حالت انتخاب چندگانه:
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.users_list.addItem(item)

    def save_finance(self):
        total_income = 0.0
        total_expense = 0.0
        # جمع آوری درآمدها:
        for label, widget in self.income_inputs.items():
            try:
                val = float(widget.text().strip()) if widget.text().strip() != "" else 0.0
                if val < 0:  # درصورتی که عدد منفی است
                    QMessageBox.warning(self, "خطا", f"مقدار {label} باید عددی مثبت باشد.")
                    return
                total_income += val
            except ValueError:
                QMessageBox.warning(self, "خطا", f"مقدار {label} عدد صحیح نیست.")
                return

        # جمع آوری هزینه‌ها:
        for label, widget in self.expense_inputs.items():
            try:
                val = float(widget.text().strip()) if widget.text().strip() != "" else 0.0
                if val < 0:
                    QMessageBox.warning(self, "خطا", f"مقدار {label} باید عددی مثبت باشد.")
                    return
                total_expense += val
            except ValueError:
                QMessageBox.warning(self, "خطا", f"مقدار {label} عدد صحیح نیست.")
                return

        net_profit = total_income - total_expense

        # اختصاص کاربران انتخاب شده
        selected_user_ids = []
        for index in range(self.users_list.count()):
            item = self.users_list.item(index)
            if item.checkState() == Qt.Checked:
                selected_user_ids.append(item.data(Qt.UserRole))
        
        # ذخیره یا به روزرسانی اطلاعات مالی پروژه در دیتابیس
        project = self.session.query(Project).filter_by(id=self.project_id).first()
        if project:
            # در اینجا فرض می‌کنیم که ستون net_profit در مدل Project وجود دارد.
            project.net_profit = net_profit
            self.session.commit()

            # اختصاص کاربران به پروژه: (اینجا به صورت ساده فرض می‌کنیم که مدل ProjectUser وجود دارد)
            # ابتدا کاربران مرتبط به این پروژه را پاک می‌کنیم.
            self.session.query(ProjectUser).filter_by(project_id=self.project_id).delete()
            for user_id in selected_user_ids:
                new_assignment = ProjectUser(project_id=self.project_id, user_id=user_id)
                self.session.add(new_assignment)
            self.session.commit()
            QMessageBox.information(self, "موفقیت", f"منابع مالی ذخیره شد. سود واقعی پروژه: {net_profit}")
        else:
            QMessageBox.warning(self, "خطا", "پروژه‌ای پیدا نشد.")
            return

        self.accept()


################################################################################
# کلاس اصلی پنجره
################################################################################
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        initialize_database()
        self.engine = get_engine()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('سامانه مدیریت پروژه و کاربران')
        self.setGeometry(100, 100, 900, 600)

        self.tabs = QTabWidget()
        
        # تب مدیریت پروژه‌ها
        self.projects_tab = QWidget()
        self.init_projects_tab()
        self.tabs.addTab(self.projects_tab, "مدیریت پروژه‌ها")
        
        # تب مدیریت کاربران
        self.users_tab = QWidget()
        self.init_users_tab()
        self.tabs.addTab(self.users_tab, "مدیریت کاربران")
        
        # تب ویرایش/حذف (پروژه‌ها و کاربران)
        self.edit_tab = QWidget()
        self.init_edit_tab()
        self.tabs.addTab(self.edit_tab, "ویرایش/حذف")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    ###########################################
    # تب مدیریت پروژه‌ها
    ###########################################
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
        
        # دکمه برای افزودن منابع مالی به پروژه (در صورت ثبت پروژه)
        self.add_finance_button = QPushButton("افزودن منابع مالی و اختصاص کاربران به پروژه")
        self.add_finance_button.clicked.connect(self.open_finance_dialog)
        layout.addWidget(self.add_finance_button)
        
        # جدول نمایش پروژه‌ها
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(4)
        self.projects_table.setHorizontalHeaderLabels(["شناسه", "نام", "توضیحات", "سود واقعی"])
        self.load_projects()
        layout.addWidget(self.projects_table)
        
        self.projects_tab.setLayout(layout)
    
    def add_project(self):
        name = self.project_name_input.text().strip()
        description = self.project_description_input.text().strip()
        if name:
            # فرض بر این است که مدل Project ستون net_profit را نیز در نظر دارد.
            new_project = Project(name=name, description=description, net_profit=0.0)
            self.session.add(new_project)
            self.session.commit()
            QMessageBox.information(self, 'موفقیت', 'پروژه افزوده شد.')
            self.project_name_input.clear()
            self.project_description_input.clear()
            self.load_projects()
            self.load_project_combo_edit()  # آپدیت کامبوی مربوط به تب ویرایش
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
            # نمایش سود واقعی؛ اگر مقدار None باشد، نمایش 0
            net_profit = project.net_profit if project.net_profit is not None else 0.0
            self.projects_table.setItem(row_position, 3, QTableWidgetItem(str(net_profit)))
    
    def open_finance_dialog(self):
        # بازگردانی شناسه پروژه انتخاب شده بر اساس انتخاب در جدول
        current_row = self.projects_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "انتخاب پروژه", "لطفاً ابتدا یک پروژه از جدول انتخاب کنید.")
            return
        # ستون صفر حاوی شناسه پروژه است
        project_id = int(self.projects_table.item(current_row, 0).text())
        dialog = FinanceDialog(self, project_id, self.session)
        if dialog.exec_() == QDialog.Accepted:
            self.load_projects()  # پس از ذخیره اطلاعات، جدول پروژه به روز شود.
    
    ###########################################
    # تب مدیریت کاربران
    ###########################################
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
            self.load_user_combo_edit()  # آپدیت کامبوی مربوط به تب ویرایش
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
    
    ###########################################
    # تب ویرایش/حذف (پروژه‌ها و کاربران)
    ###########################################
    def init_edit_tab(self):
        layout = QVBoxLayout()
        
        # بخش ویرایش/حذف پروژه‌ها
        layout.addWidget(QLabel("ویرایش/حذف پروژه‌ها"))
        project_edit_layout = QHBoxLayout()
        
        # یک کامبو برای انتخاب پروژه جهت ویرایش یا حذف
        self.project_combo_edit = QComboBox()
        self.load_project_combo_edit()
        project_edit_layout.addWidget(self.project_combo_edit)
        
        self.edit_project_button = QPushButton("ویرایش پروژه")
        self.edit_project_button.clicked.connect(self.edit_project)
        project_edit_layout.addWidget(self.edit_project_button)

        self.delete_project_button = QPushButton("حذف پروژه")
        self.delete_project_button.clicked.connect(self.delete_project)
        project_edit_layout.addWidget(self.delete_project_button)
        
        layout.addLayout(project_edit_layout)
        
        # بخش ویرایش/حذف کاربران
        layout.addWidget(QLabel("ویرایش/حذف کاربران"))
        user_edit_layout = QHBoxLayout()
        
        self.user_combo_edit = QComboBox()
        self.load_user_combo_edit()
        user_edit_layout.addWidget(self.user_combo_edit)
        
        self.edit_user_button = QPushButton("ویرایش کاربر")
        self.edit_user_button.clicked.connect(self.edit_user)
        user_edit_layout.addWidget(self.edit_user_button)

        self.delete_user_button = QPushButton("حذف کاربر")
        self.delete_user_button.clicked.connect(self.delete_user)
        user_edit_layout.addWidget(self.delete_user_button)
        
        layout.addLayout(user_edit_layout)
        
        self.edit_tab.setLayout(layout)

    # متدهای کمکی برای بروزرسانی کامبوهای تب ویرایش
    def load_project_combo_edit(self):
        if hasattr(self, 'project_combo_edit'):
            self.project_combo_edit.clear()
            projects = self.session.query(Project).all()
            for project in projects:
                self.project_combo_edit.addItem(f"{project.id} - {project.name}", project.id)

    def load_user_combo_edit(self):
        if hasattr(self, 'user_combo_edit'):
            self.user_combo_edit.clear()
            users = self.session.query(User).all()
            for user in users:
                self.user_combo_edit.addItem(f"{user.id} - {user.name}", user.id)

    # متدهای ویرایش و حذف پروژه‌ها
    def edit_project(self):
        project_index = self.project_combo_edit.currentIndex()
        project_id = self.project_combo_edit.itemData(project_index)
        project = self.session.query(Project).filter_by(id=project_id).first()
        if project:
            new_name, ok1 = QInputDialog.getText(self, "ویرایش پروژه", "نام جدید پروژه:", QLineEdit.Normal, project.name)
            if ok1 and new_name.strip():
                new_description, ok2 = QInputDialog.getText(self, "ویرایش پروژه", "توضیحات جدید پروژه:", QLineEdit.Normal, project.description if project.description else "")
                if ok2:
                    project.name = new_name.strip()
                    project.description = new_description.strip()
                    self.session.commit()
                    QMessageBox.information(self, 'موفقیت', 'پروژه ویرایش شد.')
                    self.load_projects()
                    self.load_project_combo_edit()
        else:
            QMessageBox.warning(self, 'خطا', 'پروژه‌ای انتخاب نشده است.')

    def delete_project(self):
        project_index = self.project_combo_edit.currentIndex()
        project_id = self.project_combo_edit.itemData(project_index)
        project = self.session.query(Project).filter_by(id=project_id).first()
        if project:
            confirm = QMessageBox.question(self, 'حذف پروژه', f"آیا مطمئنید که می‌خواهید پروژه '{project.name}' را حذف کنید؟", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.session.delete(project)
                self.session.commit()
                QMessageBox.information(self, 'موفقیت', 'پروژه حذف شد.')
                self.load_projects()
                self.load_project_combo_edit()
        else:
            QMessageBox.warning(self, 'خطا', 'پروژه‌ای انتخاب نشده است.')
    
    # متدهای ویرایش و حذف کاربران
    def edit_user(self):
        index = self.user_combo_edit.currentIndex()
        user_id = self.user_combo_edit.itemData(index)
        user = self.session.query(User).filter_by(id=user_id).first()
        if user:
            new_name, ok1 = QInputDialog.getText(self, "ویرایش کاربر", "نام جدید کاربر:", QLineEdit.Normal, user.name)
            if ok1 and new_name.strip():
                new_role, ok2 = QInputDialog.getText(self, "ویرایش کاربر", "سمت جدید کاربر:", QLineEdit.Normal, user.role)
                if ok2:
                    user.name = new_name.strip()
                    user.role = new_role.strip()
                    self.session.commit()
                    QMessageBox.information(self, 'موفقیت', 'کاربر ویرایش شد.')
                    self.load_users()
                    self.load_user_combo_edit()
        else:
            QMessageBox.warning(self, 'خطا', 'کاربر انتخاب نشده است.')

    def delete_user(self):
        index = self.user_combo_edit.currentIndex()
        user_id = self.user_combo_edit.itemData(index)
        user = self.session.query(User).filter_by(id=user_id).first()
        if user:
            confirm = QMessageBox.question(self, 'حذف کاربر', f"آیا مطمئنید که می‌خواهید کاربر '{user.name}' را حذف کنید؟", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.session.delete(user)
                self.session.commit()
                QMessageBox.information(self, 'موفقیت', 'کاربر حذف شد.')
                self.load_users()
                self.load_user_combo_edit()
        else:
            QMessageBox.warning(self, 'خطا', 'کاربر انتخاب نشده است.')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
