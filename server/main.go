package main

import (
	"fmt"
	// jwtware "github.com/gofiber/contrib/jwt"
	"github.com/gofiber/fiber/v2"
	"github.com/minio/minio-go/v7"
	"gorm.io/driver/postgres"

	"log"
	"os"
	"strings"
	"time"

	"github.com/bestchayapol/DishDive/internal/entities"
	"github.com/bestchayapol/DishDive/internal/handler"
	"github.com/bestchayapol/DishDive/internal/repository"
	"github.com/bestchayapol/DishDive/internal/service"
	"github.com/minio/minio-go/v7/pkg/credentials"

	"github.com/spf13/viper"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

func main() {
	loadDotEnv()
	initTimeZone()
	initConfig()
	jwtSecret := viper.GetString("jwt.jwtSecret")
	dsn := fmt.Sprintf("host=%v port=%v user=%v password=%v dbname=%v sslmode=disable TimeZone=Asia/Bangkok",
		viper.GetString("db.host"),
		viper.GetInt("db.port"),
		viper.GetString("db.username"),
		viper.GetString("db.password"),
		viper.GetString("db.database"),
	)
	log.Println(dsn)

	// Configure GORM logger to reduce SLOW SQL noise at startup (schema introspection can be slow)
	gormLogger := logger.New(
		log.New(os.Stdout, "", log.LstdFlags),
		logger.Config{
			SlowThreshold:             time.Second,  // only log queries slower than 1s
			LogLevel:                  logger.Error, // log errors only
			IgnoreRecordNotFoundError: true,         // don't log 'record not found' as errors
			Colorful:                  true,
		},
	)
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{Logger: gormLogger})
	if err != nil {
		panic("❌ Failed to connect to database: " + err.Error())
	}

	// AutoMigrate all entities
	err = db.AutoMigrate(
		&entities.User{},
		&entities.Restaurant{},
		&entities.RestaurantLocation{},
		&entities.Dish{},
		&entities.DishAlias{},
		&entities.Keyword{},
		&entities.KeywordAlias{},
		&entities.Favorite{},
		&entities.DishKeyword{},
		&entities.PreferenceBlacklist{},
		&entities.UserReview{},
		&entities.ReviewDish{},
		&entities.ReviewDishKeyword{},
		&entities.WebReview{},
		&entities.ReviewExtract{},
		&entities.CuisineImage{},
	)
	if err != nil {
		panic("❌ Failed to AutoMigrate entities: " + err.Error())
	}

	log.Println("🎉 All migrations completed successfully!")

	minioEndpoint := fmt.Sprintf("%s:%d", viper.GetString("minio.host"), viper.GetInt("minio.port"))
	minioClient, err := minio.New(minioEndpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(viper.GetString("minio.accessKey"), viper.GetString("minio.secretKey"), ""),
		Secure: false, // change to true if using HTTPS
	})
	if err != nil {
		log.Fatalln(err)
	}
	log.Println("✅ DishDive Minio connected")

	uploadService := service.NewUploadService(minioClient)
	storageHandler := handler.NewStorageHandler(uploadService)

	userRepositoryDB := repository.NewUserRepositoryDB(db)
	foodRepositoryDB := repository.NewFoodRepositoryDB(db)
	recommendRepositoryDB := repository.NewRecommendRepositoryDB(db)

	userService := service.NewUserService(userRepositoryDB, recommendRepositoryDB, jwtSecret)
	foodService := service.NewFoodService(foodRepositoryDB, recommendRepositoryDB)
	recommendService := service.NewRecommendService(foodRepositoryDB, recommendRepositoryDB)

	userHandler := handler.NewUserHandler(userService, jwtSecret, uploadService)
	foodHandler := handler.NewFoodHandler(foodService, recommendService)
	recommendHandler := handler.NewRecommendHandler(recommendService)

	app := fiber.New()

	// app.Use(func(c *fiber.Ctx) error {
	// 	if c.Path() != "/Register" && c.Path() != "/Login" {
	// 		jwtMiddleware := jwtware.New(jwtware.Config{
	// 			SigningKey: jwtware.SigningKey{Key: []byte(jwtSecret)},
	// 			ErrorHandler: func(c *fiber.Ctx, err error) error {
	// 				return fiber.ErrUnauthorized
	// 			},
	// 		})
	// 		return jwtMiddleware(c)
	// 	}
	// 	return c.Next()
	// })

	//Endpoint ###########################################################################

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
	// Food endpoints
	app.Post("/SearchRestaurantsByDish", foodHandler.SearchRestaurantsByDish)
	app.Get("/GetRestaurantList", foodHandler.GetRestaurantList)
	app.Get("/GetRestaurantMenu/:resID", foodHandler.GetRestaurantMenu)           // requires ?userID=
	app.Get("/GetRestaurantLocations/:resID", foodHandler.GetRestaurantLocations) // requires ?user_lat=&user_lng= ; untested// requires ?userID=
	app.Get("/GetDishDetail/:dishID", foodHandler.GetDishDetail)                  // requires ?userID=
	app.Get("/GetFavoriteDishes/:userID", foodHandler.GetFavoriteDishes)
	app.Post("/AddFavorite", foodHandler.AddFavorite)
	app.Delete("/RemoveFavorite", foodHandler.RemoveFavorite)
	// app.Post("/AddOrUpdateLocation", foodHandler.AddOrUpdateLocation)

	//#####################################################################################
	// Recommend endpoints
	// New unified settings endpoints
	app.Get("/GetUserSettings/:userID", recommendHandler.GetUserSettings)
	app.Post("/UpdateUserSettings/:userID", recommendHandler.UpdateUserSettings)
	app.Get("/GetUserENGroupStatus/:userID", recommendHandler.GetUserENGroupStatus)

	// Review and recommendation endpoints
	app.Get("/GetDishReviewPage/:dishID", recommendHandler.GetDishReviewPage)
	app.Post("/SubmitReview", recommendHandler.SubmitReview)
	app.Get("/GetRecommendedDishes/:userID", recommendHandler.GetRecommendedDishes)

	// Utilities
	app.Get("/ReviewExtractStatus", recommendHandler.GetReviewExtractStatus)                // ?review_id=123
	app.Get("/GetReviewNormalizationStatus", recommendHandler.GetReviewNormalizationStatus) // ?review_id=123
	app.Get("/GetReviewProcessingStatus", recommendHandler.GetReviewProcessingStatus)       // ?review_id=123
	app.Get("/EnvStatus", recommendHandler.GetEnvStatus)
	app.Get("/GetLatestReviewExtract", recommendHandler.GetLatestReviewExtract) // ?review_id=123

	//#####################################################################################

	log.Printf("DishDive running at port:  %v", viper.GetInt("app.port"))
	app.Listen(fmt.Sprintf(":%v", viper.GetInt("app.port")))

}

func initConfig() {
	viper.SetConfigName("config") // config.yaml
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")        // current directory
	viper.AddConfigPath("./config") // optional extra path

	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	viper.AutomaticEnv()

	if err := viper.ReadInConfig(); err != nil {
		log.Printf("[config] could not read config file: %v", err)
	}

	secret := viper.GetString("jwt.jwtSecret")
	if secret == "" {
		log.Println("[config] jwt.jwtSecret is EMPTY")
	}
}

func initTimeZone() {
	ict, err := time.LoadLocation("Asia/Bangkok")
	if err != nil {
		panic(err)
	}

	time.Local = ict
}

// loadDotEnv provides a tiny .env reader so you can persist secrets like OPENAI_API_KEY
// in a local file without manually exporting them every session. It looks for ./.env and ../.env.
func loadDotEnv() {
	candidates := []string{".env", "../.env"}
	for _, p := range candidates {
		b, err := os.ReadFile(p)
		if err != nil {
			continue
		}
		lines := strings.Split(string(b), "\n")
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if line == "" || strings.HasPrefix(line, "#") {
				continue
			}
			// Split on first '=' only
			eq := strings.IndexRune(line, '=')
			if eq <= 0 {
				continue
			}
			k := strings.TrimSpace(line[:eq])
			v := strings.TrimSpace(line[eq+1:])
			// strip optional surrounding quotes
			if len(v) >= 2 {
				if (v[0] == '"' && v[len(v)-1] == '"') || (v[0] == '\'' && v[len(v)-1] == '\'') {
					v = v[1 : len(v)-1]
				}
			}
			// Don't override if already set in environment
			if os.Getenv(k) == "" {
				_ = os.Setenv(k, v)
			}
		}
		log.Printf("[env] loaded variables from %s", p)
		break
	}
}
