# 🚀 Floating Widget Integration Guide: Sysforge

This guide explains the architectural changes made to decouple authentication from the **AI Chatbot MVP**, making it accessible as a public floating widget inside your main **Sysforge** application, while maintaining secure administrative dashboards for knowledge base uploads.

---

## 🛠️ Summary of Changes Made

### 1. Database Schema
*   **Nullable Session ForeignKey**: Modified the `ChatSession` model's `user` field in `backend/api/models.py` to be nullable (`null=True, blank=True`). This allows database records to represent guest sessions that are not associated with any logged-in user.
*   **Applied Migration**: Generated and applied the database schema update (`api.0002_alter_chatsession_user`) directly to PostgreSQL.

### 2. Backend API
*   **Public Access to Chat, FAQs, and Guides**: Updated `backend/api/views.py` to set the permission class to `permissions.AllowAny` on public endpoints:
    *   `ChatSessionListCreateView`
    *   `ChatSessionDetailView`
    *   `ChatMessageListView`
    *   `ChatQueryView`
    *   `FAQListCreateView` (GET method)
    *   `NavigationGuideListCreateView` (GET method)
*   **Session Management Isolation**:
    *   **Authenticated Admins/Users**: The APIs continue to save and filter sessions using `self.request.user`, keeping history private to logged-in users.
    *   **Anonymous Guest Users**: Sessions are saved with `user=None`. Guests only see messages within their own guest session.
*   **Session ID Return via SSE**: Modified the `query_stream` method in `backend/api/rag.py` and `ChatQueryView` in `views.py` to return the newly created `session_id` inside the final `'done'` metadata block of the SSE stream. This allows the guest browser to attach all future prompts to the same session.
*   **CORS & Clickjacking Protection**:
    *   **CORS**: Automatically allows all origins when in development mode (`DEBUG=True`).
    *   **Clickjacking (X-Frame)**: Configured `X_FRAME_OPTIONS = "ALLOWALL"` in `settings.py` so you can embed the chatbot as an `<iframe>` inside your main Sysforge application.

### 3. Frontend App
*   **Removed Home Route Protection**: Updated `frontend/src/App.jsx` to render `<ChatPage />` directly at `/` without the `<ProtectedRoute>` wrapper. Standard visitors load the chatbot instantly.
*   **Added Admin Portal Navigation**: Added a beautifully styled, glassmorphic **"Admin Portal"** link in the top-right corner of the home page.
    *   If the user is already authenticated as Admin, clicking this routes them straight to the `Admin Dashboard` at `/admin`.
    *   If they are unauthenticated, they are redirected to `/login`, where they can enter Admin credentials to manage FAQs, navigation guides, and upload PDF documentation.
*   **Guest Session Persistence**: Updated `ChatWidget.jsx`'s `onDone` callback to extract the newly created `session_id` from the SSE final block and update the `activeSession` state. This maintains continuous conversational context across messages.
*   **Clean Guest UI**: Hides the "Logout" button inside the chatbot widget if no user is signed in, and simplifies the footer to show only the Ollama provider details instead of a blank username.

---

## 🎨 How to Embed as a Floating Button in Sysforge

Since `X-Frame-Options` is set to `ALLOWALL` and standard endpoints are public, you can embed the chatbot widget in Sysforge in two ways.

### Method A: Embedded iframe (Recommended for simplicity)
You can inject a hidden or absolute floating button in Sysforge which toggle-reveals an `<iframe>` pointing to your chatbot deployment.

```html
<!-- Put this in the main HTML layout of Sysforge -->
<div id="sysforge-chatbot-container" style="position: fixed; bottom: 24px; right: 24px; z-index: 9999; font-family: sans-serif;">
  <!-- Floating Bubble Button -->
  <button id="chatbot-toggle" style="width: 56px; height: 56px; border-radius: 50%; background: #2563eb; color: white; border: none; cursor: pointer; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); display: flex; align-items: center; justify-content: center; font-size: 24px; transition: transform 0.2s;" onclick="toggleChatbot()">
    💬
  </button>
  
  <!-- Embedded Chatbot iframe -->
  <iframe id="chatbot-frame" src="http://localhost:3000/" style="display: none; width: 420px; height: 600px; border: none; border-radius: 16px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4); margin-bottom: 16px; position: absolute; bottom: 70px; right: 0;"></iframe>
</div>

<script>
  function toggleChatbot() {
    const frame = document.getElementById('chatbot-frame');
    const button = document.getElementById('chatbot-toggle');
    if (frame.style.display === 'none') {
      frame.style.display = 'block';
      button.innerHTML = '❌';
      button.style.transform = 'rotate(90deg)';
    } else {
      frame.style.display = 'none';
      button.innerHTML = '💬';
      button.style.transform = 'rotate(0deg)';
    }
  }
</script>
```

### Method B: Direct Script Import (Alternative)
If you prefer not to use an iframe, you can compile the React components in the chatbot's `frontend` directory as a bundled library (e.g. using Vite library build configuration) and load it inside Sysforge as a JS script:
1. Wrap `ChatWidget` with `AuthProvider` inside a single standalone React component.
2. Build the frontend as a single JS bundle: `npm run build`.
3. Import the compiled CSS and JS directly in Sysforge.

---

## 🚀 Running the App Locally

To test everything on your laptop:

1.  **Start the Backend**:
    ```bash
    cd backend
    source venv/bin/activate
    python manage.py runserver
    ```
2.  **Start the Frontend**:
    ```bash
    cd frontend
    npm run dev
    ```
3.  **Interact**:
    *   Open `http://localhost:3000/` (or the port Vite starts on).
    *   Chat immediately without signing in!
    *   Click **Admin Portal** in the top right to sign in and upload data using:
        *   **Username**: `admin`
        *   **Password**: `admin123`
