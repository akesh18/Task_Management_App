from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.database import engine, Base
from app import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Task Management System")

app.include_router(auth.router)

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Manager App</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen p-6">
    <div class="max-w-3xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <h1 class="text-2xl font-bold mb-4 text-center text-blue-600">📝 Task Management Dashboard</h1>
        
        <div id="authSection" class="mb-6 p-4 border rounded bg-gray-50">
            <h2 class="font-semibold mb-2">1-Click Login / Account</h2>
            <input id="username" type="text" placeholder="Username" class="border p-2 rounded mr-2 w-1/3">
            <input id="password" type="password" placeholder="Password" class="border p-2 rounded mr-2 w-1/3">
            <button onclick="login()" class="bg-blue-500 text-white px-4 py-2 rounded">Login</button>
            <button onclick="signup()" class="bg-gray-500 text-white px-4 py-2 rounded">Signup</button>
        </div>

        <div id="taskForm" class="mb-6 hidden">
            <h2 class="font-semibold mb-2">Add New Task</h2>
            <input id="taskTitle" type="text" placeholder="Task Title" class="border p-2 rounded w-full mb-2">
            <textarea id="taskDesc" placeholder="Task Description" class="border p-2 rounded w-full mb-2"></textarea>
            <button onclick="addTask()" class="bg-green-500 text-white px-4 py-2 rounded w-full">Add Task</button>
        </div>

        <div id="taskList"></div>
        <div id="adminDashboard" class="mt-8 hidden"></div>
    </div>

    <script>
        let token = localStorage.getItem("token") || "";

        if(token) {
            showTasks();
            checkAdmin();
        }

        async function login() {
            const u = document.getElementById("username").value;
            const p = document.getElementById("password").value;
            const formData = new URLSearchParams();
            formData.append("username", u);
            formData.append("password", p);

            const res = await fetch("/login", { method: "POST", body: formData });
            const data = await res.json();
            if(res.ok) {
                token = data.access_token;
                localStorage.setItem("token", token);
                alert("Logged in successfully!");
                showTasks();
                checkAdmin();
            } else {
                alert("Login failed!");
            }
        }

        async function signup() {
            const u = document.getElementById("username").value;
            const p = document.getElementById("password").value;
            const res = await fetch("/signup", { 
                method: "POST", 
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username: u, password: p}) 
            });
            if(res.ok) alert("Signup Successful! Now Login.");
            else alert("Signup failed!");
        }

        async function showTasks() {
            document.getElementById("taskForm").classList.remove("hidden");
            const res = await fetch("/tasks/", { headers: { "Authorization": "Bearer " + token } });
            const tasks = await res.json();
            let html = "<h2 class='font-semibold mb-2'>Your Tasks:</h2>";
            tasks.forEach(t => {
                html += `<div class="p-3 border rounded mb-2 flex justify-between items-center bg-white shadow-sm">
                    <div>
                        <div class="font-bold">${t.title}</div>
                        <div class="text-sm text-gray-600">${t.description || ''}</div>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="editTask(${t.id}, '${t.title}', '${t.description || ''}')" class="bg-yellow-500 text-white px-2 py-1 rounded text-sm">Edit</button>
                        <button onclick="deleteTask(${t.id})" class="bg-red-500 text-white px-2 py-1 rounded text-sm">Delete</button>
                    </div>
                </div>`;
            });
            document.getElementById("taskList").innerHTML = html;
        }

        async function checkAdmin() {
            const res = await fetch("/admin/users-overview", {
                headers: { "Authorization": "Bearer " + token }
            });
            
            if (res.ok) {
                const data = await res.json();
                let adminHtml = `
                <div class="border-t-2 pt-4">
                    <h2 class="text-xl font-bold text-red-600 mb-4">👑 Super Admin Dashboard</h2>
                    <table class="w-full border-collapse border border-gray-300 bg-white shadow-sm">
                        <thead>
                            <tr class="bg-gray-200 text-left">
                                <th class="p-2 border">ID</th>
                                <th class="p-2 border">Username</th>
                                <th class="p-2 border">Role</th>
                                <th class="p-2 border">Total Tasks</th>
                            </tr>
                        </thead>
                        <tbody>`;
                        
                data.forEach(u => {
                    adminHtml += `
                        <tr>
                            <td class="p-2 border">${u.id}</td>
                            <td class="p-2 border font-semibold">${u.username}</td>
                            <td class="p-2 border">${u.is_admin ? '<span class="text-red-500 font-bold">Admin</span>' : 'User'}</td>
                            <td class="p-2 border">${u.task_count}</td>
                        </tr>`;
                });

                adminHtml += `</tbody></table></div>`;
                const adminDiv = document.getElementById("adminDashboard");
                adminDiv.innerHTML = adminHtml;
                adminDiv.classList.remove("hidden");
            } else {
                document.getElementById("adminDashboard").classList.add("hidden");
            }
        }

        async function addTask() {
            const title = document.getElementById("taskTitle").value;
            const description = document.getElementById("taskDesc").value;
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
                headers: { 
                    "Content-Type": "application/json", 
                    "Authorization": "Bearer " + token 
                },
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
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return html_content

