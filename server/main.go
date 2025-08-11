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

	_"github.com/go-sql-driver/mysql"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"

	"github.com/spf13/viper"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

const jwtSecret = "DishDiveSecret"

func main() {
	initTimeZone()
	initConfig()
	dbUser := viper.GetString("db.username")
	dbPass := viper.GetString("db.password")
	dbHost := viper.GetString("db.host")
	dbPort := viper.GetInt("db.port")
	dbName := viper.GetString("db.database")

	// Prefer IPv4 for localhost to avoid ::1 issues on Windows
	if strings.EqualFold(dbHost, "localhost") {
		dbHost = "127.0.0.1"
	}

	// Ensure DB exists
	if err := ensureDatabase(dbUser, dbPass, dbHost, dbPort, dbName); err != nil {
		log.Fatalf("failed ensuring database (%s:%d as %s): %v", dbHost, dbPort, dbUser, err)
	}

	dsn := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?parseTime=true&charset=utf8mb4&loc=Local", dbUser, dbPass, dbHost, dbPort, dbName)
	log.Println(dsn)

	db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatalf("Failed to connect database: %v", err)
	}

	err = db.AutoMigrate(&entities.User{})
	if err != nil {
		panic("Failed to AutoMigrate User")
	}

	err = db.AutoMigrate(&entities.Item{})
	if err != nil {
		panic("Failed to AutoMigrate Item")
	}

	err = db.AutoMigrate(&entities.Message{})
	if err != nil {
		panic("Failed to AutoMigrate Messages")
	}

	minioEndpoint := viper.GetString("minio.host") + ":" + viper.GetString("minio.port")
	minioAccessKey := viper.GetString("minio.accessKey")
	minioSecretKey := viper.GetString("minio.secretKey")
	minioSecure := viper.GetBool("minio.secure")
	bucket := viper.GetString("minio.bucket")

	minioClient, err := minio.New(minioEndpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(minioAccessKey, minioSecretKey, ""),
		Secure: minioSecure,
	})
	if err != nil {
		log.Fatalln(err)
	}
	fmt.Println("Minio connected")

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
	itemRepositoryDB := repository.NewItemRepositoryDB(db)
	messageRepositoryDB := repository.NewMessageRepositoryDB(db)

	userService := service.NewUserService(userRepositoryDB, jwtSecret)
	itemService := service.NewItemService(itemRepositoryDB)
	messageService := service.NewMessageService(messageRepositoryDB)
	userHandler := handler.NewUserHandler(userService, jwtSecret, uploadSvc)
	itemHandler := handler.NewItemHandler(itemService, jwtSecret, uploadSvc)
	messageHandler := handler.NewMessageHandler(messageService, jwtSecret)

	app := fiber.New()

	// Enable CORS for frontend development
	app.Use(cors.New(cors.Config{
		AllowOrigins:     "*", // set to your frontend origin in production
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

	app.Get("/GetItems", itemHandler.GetItems)
	app.Get("/GetItemByItemId/:ItemID", itemHandler.GetItemByItemId)
	app.Get("/GetItemByUserID/:UserID", itemHandler.GetItemByUserId)

	app.Get("/GetMessages", messageHandler.GetMessages)
	app.Get("/GetMessageByUserId/:UserID", messageHandler.GetMessageByUserId)
	app.Get("/GetMessageByMsgId/:MsgID", messageHandler.GetMessageByMsgId)

	app.Post("/upload", storageHandler.UploadFile)

	//////////////////////////////////////////////////////////////////////////////////////

	// Endpoint for project
	app.Post("/Register", userHandler.Register)
	app.Post("/Login", userHandler.Login)

	app.Get("/GetCurrentUser", userHandler.GetCurrentUser) //#
	app.Get("/GetProfileOfCurrentUserByUserId/:UserID", userHandler.GetProfileOfCurrentUserByUserId)
	app.Get("/GetEditUserProfileByUserId/:UserID", userHandler.GetEditUserProfileByUserId)
	app.Patch("/PatchEditUserProfileByUserId/:UserID", userHandler.PatchEditUserProfileByUserId)

	app.Get("/GetItemDetailsByItemId/:ItemID", itemHandler.GetItemDetailsByItemId)

	app.Get("/GetItemsOfCurrentUser", itemHandler.GetItemsOfCurrentUser)               //#
	app.Get("/GetDonateItemsOfCurrentUser", itemHandler.GetDonateItemsOfCurrentUser)   //#
	app.Get("/GetReceiveItemsOfCurrentUser", itemHandler.GetReceiveItemsOfCurrentUser) //#

	app.Post("/PostAddItem", itemHandler.PostAddItem) //#

	app.Delete("/DeleteItemByItemId/:ItemID", itemHandler.DeleteItemByItemId)

	app.Get("/GetMarketPlace", itemHandler.GetMarketPlace)               //#
	app.Get("/GetDonateMarketPlace", itemHandler.GetDonateMarketPlace)   //#
	app.Get("/GetReceiveMarketPlace", itemHandler.GetReceiveMarketPlace) //#

	app.Put("/PutAsk/:ItemID/:AskByUserID", itemHandler.PutAskByItemIdAndPostAskMessage)

	app.Get("/GetMessagePageOfCurrentUser", messageHandler.GetMessagePageOfCurrentUser)                              //#
	app.Get("/GetConversationOfCurrentUserByOtherId/:OtherID", messageHandler.GetConversationOfCurrentUserByOtherID) //#
	app.Post("/PostMessage/:ReceiverID", messageHandler.PostMessage)

	app.Put("/PutTransactionReady/:ItemID", itemHandler.PutTransactionReady)       //#
	app.Put("/PutCompleteTransaction/:ItemID", itemHandler.PutCompleteTransaction) //#

	//#####################################################################################

	log.Printf("DishDive running at port:  %v", viper.GetInt("app.port"))
	app.Listen(fmt.Sprintf(":%v", viper.GetInt("app.port")))

}

func initConfig() {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")
	viper.AutomaticEnv()
	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))

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
