# Debugging "Invalid Input Data or Image Upload Failed" Error

## 🔍 **Common Causes & Solutions**

### **1. Backend Handler Issue (Most Likely)**
The current backend handler tries to parse JSON first, but we're sending multipart form data.

**Problem in `server/internal/handler/user.go`:**
```go
func (h *userHandler) Register(c *fiber.Ctx) error {
    var request dtos.RegisterRequest
    if err := c.BodyParser(&request); err != nil {  // ❌ This fails for multipart
        return fiber.NewError(fiber.StatusBadRequest, err.Error())
    }
    // ... rest of code
}
```

**Solution - Replace the Register function with:**
```go
func (h *userHandler) Register(c *fiber.Ctx) error {
    // Parse multipart form data directly
    username := c.FormValue("user_name")
    password := c.FormValue("password_hash")

    // Validate required fields
    if username == "" {
        return fiber.NewError(fiber.StatusBadRequest, "Username is required")
    }
    if password == "" {
        return fiber.NewError(fiber.StatusBadRequest, "Password is required")
    }

    // Check if a file is uploaded
    file, err := c.FormFile("file")
    if err != nil {
        return fiber.NewError(fiber.StatusBadRequest, "Profile picture is required")
    }

    // Call upload service to upload the file
    fileURL, err := h.uploadSer.UploadFile(file)
    if err != nil {
        return fiber.NewError(fiber.StatusInternalServerError, "Failed to upload profile picture")
    }

    // Create the register request
    request := dtos.RegisterRequest{
        Username:     &username,
        ImageLink:    fileURL,
        PasswordHash: password,
    }

    response, err := h.userSer.Register(request)
    if err != nil {
        return fiber.NewError(fiber.StatusInternalServerError, err.Error())
    }

    return c.Status(fiber.StatusCreated).JSON(response)
}
```

### **2. CORS Issues**
Add CORS middleware to your backend `main.go`:

```go
import "github.com/gofiber/fiber/v2/middleware/cors"

// Add this before your routes
app.Use(cors.New(cors.Config{
    AllowOrigins: "*",
    AllowMethods: "GET,POST,HEAD,PUT,DELETE,PATCH",
    AllowHeaders: "*",
}))
```

### **3. Network Configuration**
Check your API configuration:

**For Android Emulator:**
```dart
static const String baseUrl = 'http://10.0.2.2:8080';
```

**For Physical Device:**
```dart
static const String baseUrl = 'http://YOUR_COMPUTER_IP:8080';
```

Find your computer's IP:
- Windows: `ipconfig`
- Mac/Linux: `ifconfig`

### **4. MinIO Configuration**
Ensure MinIO is properly configured in `server/config.yaml`:

```yaml
minio:
  host: "dishdive.sit.kmutt.ac.th"
  port: 9000
  accessKey: "your_access_key"
  secretKey: "your_secret_key"
  bucket: "dishdive"
  publicURL: "https://minio.dishdive.sit.kmutt.ac.th"
```

## 🧪 **Debugging Steps**

### **Step 1: Test Basic Connectivity**
Run this in your Flutter app:

```dart
import 'package:dishdive/utils/connection_tester.dart';

// In your main() or a test button
await ConnectionTester.testBackendConnection();
await ConnectionTester.testRegisterEndpoint();
```

### **Step 2: Check Flutter Debug Console**
With the updated AuthService, you'll see detailed logs:
```
🔧 DEBUG: Starting registration...
🔧 DEBUG: Username: test_user
🔧 DEBUG: Image file: /path/to/image.jpg
🔧 DEBUG: File size: 123456 bytes
🔧 DEBUG: Payload created, sending to: http://10.0.2.2:8080/Register
```

### **Step 3: Check Backend Logs**
Add logging to your backend handler:

```go
func (h *userHandler) Register(c *fiber.Ctx) error {
    log.Println("📥 Register request received")
    log.Printf("📥 Content-Type: %s", c.Get("Content-Type"))
    log.Printf("📥 Form values: %+v", c.AllParams())
    
    // ... rest of your code
}
```

### **Step 4: Test with Curl**
Test the endpoint directly:

```bash
curl -X POST http://localhost:8080/Register \
  -F "user_name=test_user" \
  -F "password_hash=test_password" \
  -F "file=@/path/to/test_image.jpg"
```

## 🚨 **Quick Fixes to Try**

### **Fix 1: Update Backend Handler**
Replace the Register function as shown above.

### **Fix 2: Add CORS Middleware**
```go
app.Use(cors.New())
```

### **Fix 3: Check Server is Running**
```bash
cd server
go run .
# Should see: "DishDive running at port: 8080"
```

### **Fix 4: Verify Network**
- Android Emulator: Use `10.0.2.2:8080`
- Physical Device: Use your computer's IP address

### **Fix 5: Test with Simple Image**
Try with a small (< 1MB) JPG image first.

## 📱 **Testing Checklist**

- [ ] Backend server is running (`go run .`)
- [ ] Correct base URL in `api_config.dart`
- [ ] CORS middleware added to backend
- [ ] Register handler uses `c.FormValue()` instead of `c.BodyParser()`
- [ ] MinIO is accessible
- [ ] Image file is valid (< 5MB, JPG/PNG/WebP)
- [ ] Debug logs are enabled

## 🔧 **Most Likely Solution**

The issue is **99% likely** to be the backend handler trying to parse JSON instead of multipart form data. Update the Register function in `user.go` as shown above, and the error should disappear!
