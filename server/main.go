package main

import (
	"context"
	"database/sql"
	"fmt"

	jwtware "github.com/gofiber/contrib/jwt"

	//jwtware "github.com/gofiber/contrib/jwt"
	"log"
	"strings"
	"time"

	"github.com/bestchayapol/DishDive/internal/entities"
	"github.com/bestchayapol/DishDive/internal/handler"
	"github.com/bestchayapol/DishDive/internal/repository"
	"github.com/bestchayapol/DishDive/internal/service"
	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"

	_ "github.com/go-sql-driver/mysql"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"

	"github.com/joho/godotenv"
	"github.com/spf13/viper"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

const jwtSecret = "DishDiveSecret"

func main() {
	initTimeZone()
	initConfig()

	dbUser := viper.GetString("database.user")
	dbPass := viper.GetString("database.password")
	dbHost := viper.GetString("database.host")
	dbPort := viper.GetInt("database.port")
	dbName := viper.GetString("database.name")

	// Prefer IPv4 for localhost to avoid ::1 issues on Windows
	// if strings.EqualFold(dbHost, "localhost") {
	// 	dbHost = "127.0.0.1"
	// }

	// Ensure DB exists
	if err := ensureDatabase(dbUser, dbPass, dbHost, dbPort, dbName); err != nil {
		log.Fatalf("failed ensuring database (%s:%d as %s): %v", dbHost, dbPort, dbUser, err)
	}

	dsn := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?parseTime=true&charset=utf8mb4&loc=Local", dbUser, dbPass, dbHost, dbPort, dbName)
	log.Println(dsn)

	db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})

	if err := db.AutoMigrate(
		&entities.User{},
		&entities.Restaurant{},
		&entities.Dish{},
	); err != nil {
		log.Fatalf("AutoMigrate failed: %v", err)
	}

	// Build MinIO endpoint, prefer IPv4 to avoid ::1 quirks
	minioHost := viper.GetString("minio.host")
	if strings.EqualFold(minioHost, "localhost") {
		minioHost = "127.0.0.1"
	}
	minioPort := viper.GetInt("minio.port")
	minioEndpoint := fmt.Sprintf("%s:%d", minioHost, minioPort)
	minioAccessKey := viper.GetString("minio.accessKey")
	minioSecretKey := viper.GetString("minio.secretKey")
	minioSecure := viper.GetBool("minio.secure")
	bucket := viper.GetString("minio.bucket")

	// Debug (safe): show which endpoint/bucket and key length
	log.Printf("MinIO endpoint=%s secure=%v bucket=%q ak.len=%d",
		minioEndpoint, minioSecure, bucket, len(minioAccessKey))

	minioClient, err := minio.New(minioEndpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(minioAccessKey, minioSecretKey, ""),
		Secure: minioSecure,
	})
	if err != nil {
		log.Fatalln(err)
	}
	fmt.Println("Minio connected")
	// fmt.Println("AccessKey:", minioAccessKey)
	// fmt.Println("SecretKey:", minioSecretKey)

	// Ensure the bucket exists
	{
		ctx := context.Background()
		exists, err := minioClient.BucketExists(ctx, bucket)
		if err != nil {
			log.Fatalln("minio bucket check error:", err)
		}
		if !exists {
			if err := minioClient.MakeBucket(ctx, bucket, minio.MakeBucketOptions{}); err != nil {
				log.Fatalln("failed to create minio bucket:", err)
			}
		}
	}

	// Configure public URL for uploaded objects (optional)
	var publicBaseURLPtr *string
	if v := viper.GetString("minio.publicBaseURL"); v != "" {
		publicBaseURLPtr = &v
	}

	uploadSvc := service.NewUploadService(minioClient, bucket, publicBaseURLPtr)
	storageHandler := handler.NewStorageHandler(uploadSvc)

	userRepositoryDB := repository.NewUserRepositoryDB(db)

	userService := service.NewUserService(userRepositoryDB, jwtSecret)

	userHandler := handler.NewUserHandler(userService, jwtSecret, uploadSvc)

	app := fiber.New()

	// Read allowed origin from config (optional), default to localhost:3000
	frontendOrigin := viper.GetString("app.frontendOrigin")
	if frontendOrigin == "" {
		frontendOrigin = "http://localhost:3000"
	}

	// Enable CORS for frontend development (credentials allowed with explicit origin)
	app.Use(cors.New(cors.Config{
		AllowOrigins:     frontendOrigin, // e.g., http://localhost:3000
		AllowHeaders:     "Origin, Content-Type, Accept, Authorization",
		AllowMethods:     "GET,POST,PUT,PATCH,DELETE,OPTIONS",
		AllowCredentials: true,
	}))

	app.Use(func(c *fiber.Ctx) error {
		if c.Path() != "/Register" && c.Path() != "/Login" {
			jwtMiddleware := jwtware.New(jwtware.Config{
				SigningKey: jwtware.SigningKey{Key: []byte(jwtSecret)},
				ErrorHandler: func(c *fiber.Ctx, err error) error {
					return fiber.ErrUnauthorized
				},
			})
			return jwtMiddleware(c)
		}
		return c.Next()
	})

	//Endpoint ###########################################################################

	// Health check
	app.Get("/health", func(c *fiber.Ctx) error { return c.SendString("ok") })

	// Endpoint for test
	app.Get("/GetUsers", userHandler.GetUsers)
	app.Get("/GetUserByUserId/:UserID", userHandler.GetUserByUserId)
	app.Get("/GetUserByToken", userHandler.GetUserByToken) //#

	app.Post("/upload", storageHandler.UploadFile)

	//////////////////////////////////////////////////////////////////////////////////////

	// Endpoint for project
	app.Post("/Register", userHandler.Register)
	app.Post("/Login", userHandler.Login)

	app.Get("/GetCurrentUser", userHandler.GetCurrentUser) //#
	app.Get("/GetProfileOfCurrentUserByUserId/:UserID", userHandler.GetProfileOfCurrentUserByUserId)
	app.Get("/GetEditUserProfileByUserId/:UserID", userHandler.GetEditUserProfileByUserId)
	app.Patch("/PatchEditUserProfileByUserId/:UserID", userHandler.PatchEditUserProfileByUserId)

	//#####################################################################################

	log.Printf("DishDive running at port:  %v", viper.GetInt("app.port"))
	app.Listen(fmt.Sprintf(":%v", viper.GetInt("app.port")))

}

func initConfig() {
	// Load .env for local dev
	_ = godotenv.Load(".env")

	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")
	viper.AutomaticEnv()
	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))

	// Bind specific env vars used by docker-compose / MinIO to config keys
	// Allows using MINIO_ROOT_USER / MINIO_ROOT_PASSWORD / MINIO_BUCKET without changing config.yaml
	_ = viper.BindEnv("minio.accessKey", "MINIO_ROOT_USER")
	_ = viper.BindEnv("minio.secretKey", "MINIO_ROOT_PASSWORD")
	_ = viper.BindEnv("minio.bucket", "MINIO_BUCKET")

	err := viper.ReadInConfig()
	if err != nil {
		panic(err)
	}
}

func initTimeZone() {
	ict, err := time.LoadLocation("Asia/Bangkok")
	if err != nil {
		panic(err)
	}

	time.Local = ict
}

func ensureDatabase(user, pass, host string, port int, dbName string) error {
	// Connect without a DB to create it if missing
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%d)/?parseTime=true&timeout=5s", user, pass, host, port)
	sqlDB, err := sql.Open("mysql", dsn)
	if err != nil {
		return err
	}
	defer sqlDB.Close()

	if err := sqlDB.Ping(); err != nil {
		return err
	}
	_, err = sqlDB.Exec("CREATE DATABASE IF NOT EXISTS `" + dbName + "` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
	return err
}
