package main

import (
	"fmt"
	jwtware "github.com/gofiber/contrib/jwt"

	//jwtware "github.com/gofiber/contrib/jwt"
	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
	"log"
	"needful/internal/entities"
	"needful/internal/handler"
	"needful/internal/repository"
	"needful/internal/service"
	"strings"
	"time"

	"github.com/gofiber/fiber/v2"

	"github.com/spf13/viper"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

const jwtSecret = "NeedFulSecret"

func main() {
	initTimeZone()
	initConfig()
	dsn := fmt.Sprintf("%v:%v@tcp(%v:%v)/%v?parseTime=true",
		viper.GetString("db.username"),
		viper.GetString("db.password"),
		viper.GetString("db.host"),
		viper.GetInt("db.port"),
		viper.GetString("db.database"),
	)
	log.Println(dsn)

	db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})

	if err != nil {
		panic("Failed to connect database")
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

	minioClient, err := minio.New(viper.GetString("minio.host")+":"+viper.GetString("minio.port"), &minio.Options{
		Creds:  credentials.NewStaticV4("HDeAly8XddiQTvjjTRfL", "9OtiaCEOL1586uDgPAXNANDndM04ga3oMdGy7kGF", ""),
		Secure: false,
	})
	if err != nil {
		log.Fatalln(err)
	}
	fmt.Println("Minio connected")

	uploadSer := service.NewUploadService(minioClient)
	storageHandler := handler.NewStorageHandler(uploadSer)

	userRepositoryDB := repository.NewUserRepositoryDB(db)
	itemRepositoryDB := repository.NewItemRepositoryDB(db)
	messageRepositoryDB := repository.NewMessageRepositoryDB(db)

	userService := service.NewUserService(userRepositoryDB, jwtSecret)
	itemService := service.NewItemService(itemRepositoryDB)
	messageService := service.NewMessageService(messageRepositoryDB)
	uploadService := service.NewUploadService(minioClient)

	userHandler := handler.NewUserHandler(userService, jwtSecret, uploadService)
	itemHandler := handler.NewItemHandler(itemService, jwtSecret, uploadService)
	messageHandler := handler.NewMessageHandler(messageService, jwtSecret)

	app := fiber.New()

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

	log.Printf("NeedFul running at port:  %v", viper.GetInt("app.port"))
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
