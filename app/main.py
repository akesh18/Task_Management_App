from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app import auth, models, schemas
from passlib.context import CryptContext

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Task Management System")

@app.on_event("startup")
def startup_db_setup():
    db = SessionLocal()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    ADMIN_USER = "admin"
    ADMIN_PASS = "admin123"
    
    try:
        existing_admin = db.query(models.User).filter(models.User.username == ADMIN_USER).first()
        if not existing_admin:
            hashed_pw = pwd_context.hash(ADMIN_PASS)
            admin_user = models.User(username=ADMIN_USER, hashed_password=hashed_pw, is_admin=True)
            db.add(admin_user)
            db.commit()
            print("Super Admin created automatically on startup!")
    except Exception as e:
        db.rollback()
        print("Startup admin creation error:", e)
    finally:
        db.close()

app.include_router(auth.router)

# ================= TASK ENDPOINTS =================
@app.get("/tasks/")
def read_tasks(
    db: Session = Depends(auth.database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.Task).filter(models.Task.owner_id == current_user.id).all()

@app.post("/tasks/")
def create_task(
    task: schemas.TaskCreate, 
    db: Session = Depends(auth.database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    db_task = models.Task(**task.dict(), owner_id=current_user.id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.put("/tasks/{task_id}")
def update_task(
    task_id: int, 
    task: schemas.TaskCreate, 
    db: Session = Depends(auth.database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    db_task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == current_user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.title = task.title
    db_task.description = task.description
    db.commit()
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int, 
    db: Session = Depends(auth.database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    db_task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == current_user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted"}

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Manager App</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = { darkMode: 'class' }
    </script>
</head>
<body class="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 min-h-screen transition-colors duration-300">
    
    <!-- GLOBAL TOP NAVBAR WITH DARK MODE TOGGLE -->
    <nav class="w-full bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3 flex justify-between items-center shadow-sm">
        <div class="flex items-center gap-2">
            <span class="text-2xl font-bold text-blue-600 dark:text-blue-500">📝 TaskApp</span>
        </div>
        <div class="flex items-center gap-4">
            <!-- Global Dark Mode Toggle Button -->
            <button onclick="toggleDarkMode()" class="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 px-3 py-1.5 rounded-lg text-sm font-semibold shadow-sm hover:bg-gray-300 dark:hover:bg-gray-600 transition flex items-center gap-1.5">
                <span id="themeIcon">🌙</span> <span id="themeText">Dark</span>
            </button>

            <!-- User Section (Logout & Delete Account) -->
            <div id="userSection" class="hidden flex gap-2">
                <button id="deleteMyAccountBtn" onclick="deleteMyAccount()" class="bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-950 dark:text-red-300 border border-red-300 dark:border-red-800 px-3 py-1.5 rounded font-semibold text-xs shadow-sm hidden">
                    🗑️ Delete My Account
                </button>
                <button onclick="logout()" class="bg-red-500 hover:bg-red-600 text-white px-4 py-1.5 rounded font-semibold text-sm shadow">
                    🔒 Logout
                </button>
            </div>
        </div>
    </nav>

    <!-- LOGIN / AUTH UI -->
    <div id="authContainer" class="flex flex-col md:flex-row items-center justify-center min-h-[calc(100vh-65px)] px-4 hidden">
        <div class="mb-8 md:mb-0 md:mr-16 text-center md:text-left max-w-md">
            <h1 class="text-5xl font-bold text-blue-600 dark:text-blue-500 mb-4">TaskApp</h1>
            <p class="text-2xl text-gray-700 dark:text-gray-300 mb-4">Connect with your work and manage tasks efficiently.</p>
            <button onclick="showAdminLogin()" class="text-blue-600 dark:text-blue-400 font-semibold text-lg hover:underline hidden md:inline-block">Login as an Admin</button>
        </div>

        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-xl rounded-xl p-6 w-full max-w-md">
            
            <!-- User Login Form -->
            <div id="userLoginFormWrapper">
                <h2 class="text-lg text-center font-semibold mb-4 text-gray-800 dark:text-gray-200">Log in to Task management app</h2>
                <form onsubmit="event.preventDefault(); submitLogin('user');" class="flex flex-col gap-4">
                    <input id="u_username" type="text" placeholder="Username" required minlength="3" class="w-full p-3.5 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white text-lg">
                    <input id="u_password" type="password" placeholder="Password" required minlength="3" class="w-full p-3.5 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white text-lg">
                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-md text-xl mt-1 transition">Log in</button>
                </form>
                <div class="border-b border-gray-300 dark:border-gray-700 my-5"></div>
                <div class="text-center">
                    <button onclick="showSignup()" class="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-md text-lg transition inline-block">Create new account</button>
                </div>
                <div class="text-center mt-6 md:hidden">
                    <button onclick="showAdminLogin()" class="text-blue-600 dark:text-blue-400 font-semibold hover:underline">Login as an Admin</button>
                </div>
            </div>

            <!-- Admin Login Form -->
            <div id="adminLoginFormWrapper" class="hidden">
                <h2 class="text-lg text-center font-bold mb-4 text-red-600 dark:text-red-400">Admin Log in</h2>
                <form onsubmit="event.preventDefault(); submitLogin('admin');" class="flex flex-col gap-4">
                    <input id="a_username" type="text" placeholder="Admin Username" required minlength="3" class="w-full p-3.5 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 dark:bg-gray-800 dark:text-white text-lg">
                    <input id="a_password" type="password" placeholder="Admin Password" required minlength="3" class="w-full p-3.5 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 dark:bg-gray-800 dark:text-white text-lg">
                    <button type="submit" class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-md text-xl mt-1 transition">Log in as Admin</button>
                </form>
                <div class="border-b border-gray-300 dark:border-gray-700 my-5"></div>
                <div class="text-center">
                    <button onclick="showUserLogin()" class="text-blue-600 dark:text-blue-400 font-semibold hover:underline text-lg">Back to User Login</button>
                </div>
            </div>

            <!-- Signup Form -->
            <div id="signupFormWrapper" class="hidden">
                <h2 class="text-lg text-center font-semibold mb-4 text-gray-800 dark:text-gray-200">Create new account</h2>
                <form onsubmit="event.preventDefault(); submitSignupForm();" class="flex flex-col gap-4">
                    <input id="s_username" type="text" placeholder="Username" required minlength="3" class="w-full p-3.5 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800 dark:text-white text-lg">
                    <input id="s_password" type="password" placeholder="Password" required minlength="3" class="w-full p-3.5 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800 dark:text-white text-lg">
                    <button type="submit" class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 rounded-md text-xl mt-1 transition">Sign Up</button>
                </form>
                <div class="border-b border-gray-300 dark:border-gray-700 my-5"></div>
                <div class="text-center">
                    <button onclick="showUserLogin()" class="text-blue-600 dark:text-blue-400 font-semibold hover:underline text-lg">Already have an account?</button>
                </div>
            </div>

        </div>
    </div>
    
    <!-- MAIN DASHBOARD -->
    <div id="dashboardContainer" class="hidden p-6">
        <div class="max-w-3xl mx-auto bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
            <!-- Task Form -->
            <div id="taskForm" class="mb-6">
                <h2 class="font-semibold mb-2">Add New Task</h2>
                <input id="taskTitle" type="text" placeholder="Task Title" class="border p-2 rounded w-full mb-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                <textarea id="taskDesc" placeholder="Task Description" class="border p-2 rounded w-full mb-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"></textarea>
                <button onclick="addTask()" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded w-full">Add Task</button>
            </div>

            <div id="taskList"></div>
            <div id="adminDashboard" class="mt-8 hidden"></div>
        </div>
    </div>

    <script>
        let token = localStorage.getItem("token") || "";

        // Dark Mode Logic
        if (localStorage.getItem("theme") === "dark") {
            document.documentElement.classList.add("dark");
            updateThemeUI(true);
        }
        function toggleDarkMode() {
            const isDark = document.documentElement.classList.toggle("dark");
            localStorage.setItem("theme", isDark ? "dark" : "light");
            updateThemeUI(isDark);
        }
        function updateThemeUI(isDark) {
            document.getElementById("themeIcon").innerText = isDark ? "☀️" : "🌙";
            document.getElementById("themeText").innerText = isDark ? "Light" : "Dark";
        }

        if (token) {
            document.getElementById("dashboardContainer").classList.remove("hidden");
            document.getElementById("authContainer").classList.add("hidden");
            document.getElementById("userSection").classList.remove("hidden");
            showTasks();
            checkAdmin();
        } else {
            document.getElementById("dashboardContainer").classList.add("hidden");
            document.getElementById("userSection").classList.add("hidden");
            document.getElementById("authContainer").classList.remove("hidden");
            document.getElementById("authContainer").classList.add("flex");
        }

        function showUserLogin() {
            document.getElementById("userLoginFormWrapper").classList.remove("hidden");
            document.getElementById("adminLoginFormWrapper").classList.add("hidden");
            document.getElementById("signupFormWrapper").classList.add("hidden");
        }
        function showAdminLogin() {
            document.getElementById("userLoginFormWrapper").classList.add("hidden");
            document.getElementById("adminLoginFormWrapper").classList.remove("hidden");
            document.getElementById("signupFormWrapper").classList.add("hidden");
        }
        function showSignup() {
            document.getElementById("userLoginFormWrapper").classList.add("hidden");
            document.getElementById("adminLoginFormWrapper").classList.add("hidden");
            document.getElementById("signupFormWrapper").classList.remove("hidden");
        }

        function logout() {
            localStorage.removeItem("token");
            window.location.reload();
        }

        async function submitLogin(role) {
            let u, p;
            if (role === 'user') {
                u = document.getElementById("u_username").value;
                p = document.getElementById("u_password").value;
            } else {
                u = document.getElementById("a_username").value;
                p = document.getElementById("a_password").value;
            }

            const formData = new URLSearchParams();
            formData.append("username", u);
            formData.append("password", p);
            formData.append("client_id", role);

            try {
                const res = await fetch("/login", { method: "POST", body: formData });
                const data = await res.json();
                
                if (res.ok) {
                    localStorage.setItem("token", data.access_token);
                    window.location.reload();
                } else {
                    alert(data.detail || "Login failed");
                }
            } catch (err) {
                alert("Network error, please try again later.");
            }
        }

        async function submitSignupForm() {
            const u = document.getElementById("s_username").value;
            const p = document.getElementById("s_password").value;
            
            try {
                const res = await fetch("/signup", { 
                    method: "POST", 
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({username: u, password: p}) 
                });
                const data = await res.json();
                
                if (res.ok) {
                    alert("Account created successfully! You can now log in.");
                    showUserLogin();
                } else {
                    alert(data.detail || "Signup failed");
                }
            } catch (err) {
                alert("Network error, please try again later.");
            }
        }

        async function showTasks() {
            const res = await fetch("/tasks/", { headers: { "Authorization": "Bearer " + token } });
            const tasks = await res.json();
            let html = "<h2 class='font-semibold mb-2'>Your Tasks:</h2>";
            if(Array.isArray(tasks)) {
                tasks.forEach(t => {
                    html += `<div class="p-3 border rounded mb-2 flex justify-between items-center bg-white dark:bg-gray-800 dark:border-gray-700 shadow-sm">
                        <div>
                            <div class="font-bold">${t.title}</div>
                            <div class="text-sm text-gray-600 dark:text-gray-300">${t.description || ''}</div>
                        </div>
                        <div class="flex gap-2">
                            <button onclick="editTask(${t.id}, '${t.title}', '${t.description || ''}')" class="bg-yellow-500 text-white px-2 py-1 rounded text-sm">Edit</button>
                            <button onclick="deleteTask(${t.id})" class="bg-red-500 text-white px-2 py-1 rounded text-sm">Delete</button>
                        </div>
                    </div>`;
                });
            }
            document.getElementById("taskList").innerHTML = html;
        }

        async function checkAdmin() {
            const res = await fetch("/admin/users-overview", {
                headers: { "Authorization": "Bearer " + token }
            });
            const deleteBtn = document.getElementById("deleteMyAccountBtn");

            if (res.ok) {
                if (deleteBtn) deleteBtn.classList.add("hidden");
                const data = await res.json();
                let adminHtml = `
                <div class="border-t-2 pt-4 dark:border-gray-700">
                    <h2 class="text-xl font-bold text-red-600 dark:text-red-400 mb-4">👑 Super Admin Dashboard</h2>
                    <table class="w-full border-collapse border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm text-sm">
                        <thead>
                            <tr class="bg-gray-200 dark:bg-gray-700 text-left">
                                <th class="p-2 border dark:border-gray-600">ID</th>
                                <th class="p-2 border dark:border-gray-600">Username</th>
                                <th class="p-2 border dark:border-gray-600">Role</th>
                                <th class="p-2 border dark:border-gray-600">Total Tasks</th>
                                <th class="p-2 border dark:border-gray-600">Action</th>
                            </tr>
                        </thead>
                        <tbody>`;
                        
                data.forEach(u => {
                    adminHtml += `
                        <tr>
                            <td class="p-2 border dark:border-gray-700">${u.id}</td>
                            <td class="p-2 border dark:border-gray-700 font-semibold">${u.username}</td>
                            <td class="p-2 border dark:border-gray-700">${u.is_admin ? '<span class="text-red-500 font-bold">Admin</span>' : 'User'}</td>
                            <td class="p-2 border dark:border-gray-700">${u.task_count}</td>
                            <td class="p-2 border dark:border-gray-700">
                                ${u.is_admin ? '<span class="text-gray-400 text-xs">Protected</span>' : 
                                `<button onclick="deleteUserByAdmin(${u.id}, '${u.username}')" class="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs font-semibold">Delete User</button>`}
                            </td>
                        </tr>`;
                });
                adminHtml += `</tbody></table></div>`;
                const adminDiv = document.getElementById("adminDashboard");
                adminDiv.innerHTML = adminHtml;
                adminDiv.classList.remove("hidden");
            } else {
                if (deleteBtn) deleteBtn.classList.remove("hidden");
                document.getElementById("adminDashboard").classList.add("hidden");
            }
        }

        async function addTask() {
            const title = document.getElementById("taskTitle").value;
            const description = document.getElementById("taskDesc").value;
            if(!title) {
                alert("Please enter a task title!");
                return;
            }
            await fetch("/tasks/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
                body: JSON.stringify({ title, description })
            });
            document.getElementById("taskTitle").value = "";
            document.getElementById("taskDesc").value = "";
            showTasks();
            checkAdmin();
        }

        async function editTask(id, currentTitle, currentDesc) {
            const newTitle = prompt("Edit Task Title:", currentTitle);
            if (newTitle === null) return;
            const newDesc = prompt("Edit Task Description:", currentDesc);

            await fetch("/tasks/" + id, {
                method: "PUT",
                headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
                body: JSON.stringify({ title: newTitle, description: newDesc })
            });
            showTasks();
            checkAdmin();
        }

        async function deleteTask(id) {
            await fetch("/tasks/" + id, {
                method: "DELETE",
                headers: { "Authorization": "Bearer " + token }
            });
            showTasks();
            checkAdmin();
        }

        async function deleteMyAccount() {
            if(!confirm("Are you sure you want to permanently delete your account and all associated tasks?")) return;
            const res = await fetch("/users/me", {
                method: "DELETE",
                headers: { "Authorization": "Bearer " + token }
            });
            if(res.ok) {
                alert("Your account has been deleted successfully.");
                logout();
            } else {
                alert("Failed to delete account.");
            }
        }

        async function deleteUserByAdmin(userId, username) {
            if(!confirm(`Are you sure you want to delete user '${username}' and all their tasks?`)) return;
            const res = await fetch("/admin/users/" + userId, {
                method: "DELETE",
                headers: { "Authorization": "Bearer " + token }
            });
            if(res.ok) {
                alert(`User ${username} deleted successfully!`);
                checkAdmin();
                showTasks();
            } else {
                const data = await res.json();
                alert(data.detail || "Failed to delete user.");
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return html_content