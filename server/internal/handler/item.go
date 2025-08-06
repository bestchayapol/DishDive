package handler

import (
	"errors"
	"github.com/gofiber/fiber/v2"
	"needful/internal/dtos"
	"needful/internal/service"
	"needful/internal/utils"
	"strconv"
	"strings"
)

type itemHandler struct {
	itemSer   service.ItemService
	jwtSecret string
	uploadSer service.UploadService
}

func NewItemHandler(itemSer service.ItemService, jwtSecret string, uploadSer service.UploadService) itemHandler {
	return itemHandler{itemSer: itemSer, jwtSecret: jwtSecret, uploadSer: uploadSer}
}

func (h *itemHandler) GetItems(c *fiber.Ctx) error {
	itemsResponse := make([]dtos.ItemDataResponse, 0)

	items, err := h.itemSer.GetItems()
	if err != nil {
		return err
	}

	for _, item := range items {
		itemsResponse = append(itemsResponse, dtos.ItemDataResponse{
			ItemID:        item.ItemID,
			UserID:        item.UserID,
			Itemname:      item.Itemname,
			Description:   item.Description,
			ItemPic:       item.ItemPic,
			OfferType:     item.OfferType,
			AskedByUserID: item.AskedByUserID,
			AlreadyGave:   item.AlreadyGave,
		})
	}
	return c.JSON(itemsResponse)
}

func (h *itemHandler) GetItemByUserId(c *fiber.Ctx) error {

	userIDReceive, err := strconv.Atoi(c.Params("UserID"))

	itemsResponse := make([]dtos.ItemDataByUserIdResponse, 0)
	item, err := h.itemSer.GetItemByUserId(userIDReceive)
	if err != nil {
		return err
	}

	for _, item := range item {
		itemsResponse = append(itemsResponse, dtos.ItemDataByUserIdResponse{
			ItemID:        item.ItemID,
			UserID:        item.UserID,
			Itemname:      item.Itemname,
			Description:   item.Description,
			ItemPic:       item.ItemPic,
			OfferType:     item.OfferType,
			AskedByUserID: item.AskedByUserID,
			AlreadyGave:   item.AlreadyGave,
		})
	}
	return c.JSON(itemsResponse)
}

func (h *itemHandler) GetItemByItemId(c *fiber.Ctx) error {
	itemIDReceive, err := strconv.Atoi(c.Params("ItemID"))

	item, err := h.itemSer.GetItemByItemId(itemIDReceive)
	if err != nil {
		return err
	}

	itemResponse := dtos.ItemDataByItemIdResponse{
		ItemID:        item.ItemID,
		UserID:        item.UserID,
		Itemname:      item.Itemname,
		Description:   item.Description,
		ItemPic:       item.ItemPic,
		OfferType:     item.OfferType,
		AskedByUserID: item.AskedByUserID,
		AlreadyGave:   item.AlreadyGave,
	}

	return c.JSON(itemResponse)
}

//****************************************************************************

func (h *itemHandler) GetItemDetailsByItemId(c *fiber.Ctx) error {
	itemIDReceive, err := strconv.Atoi(c.Params("ItemID"))

	item, err := h.itemSer.GetItemDetailsByItemId(itemIDReceive)
	if err != nil {
		return err
	}

	itemResponse := dtos.ItemDetailsByItemIdResponse{
		ItemID:        item.ItemID,
		UserID:        item.UserID,
		Itemname:      item.Itemname,
		Description:   item.Description,
		ItemPic:       item.ItemPic,
		OfferType:     item.OfferType,
		AskedByUserID: item.AskedByUserID,
		AlreadyGave:   item.AlreadyGave,
		ConFromItemOwner: item.ConFromItemOwner,
		ConFromItemAsker: item.ConFromItemAsker,
	}

	return c.JSON(itemResponse)
}

//****************************************************************************

func (h *itemHandler) GetItemsOfCurrentUser(c *fiber.Ctx) error {
	// Extract the token from the request headers
	token := c.Get("Authorization")

	// Check if the token is empty
	if token == "" {
		return errors.New("token is missing")
	}

	// Extract the user ID from the token
	userID, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	items, err := h.itemSer.GetItemsOfCurrentUser(userID)
	if err != nil {
		return err
	}

	itemsResponse := make([]dtos.ItemsOfCurrentUserResponse, 0)
	for _, item := range items {
		itemsResponse = append(itemsResponse, dtos.ItemsOfCurrentUserResponse{
			ItemID:                  item.ItemID,
			UserID:                  item.UserID,
			Itemname:                item.Itemname,
			Description:             item.Description,
			ItemPic:                 item.ItemPic,
			OfferType:               item.OfferType,
			AskedByUserID:           item.AskedByUserID,
			AlreadyGave:             item.AlreadyGave,
			Username:                item.Username,
			UserPic:                 item.UserPic,
			UsernameOfAskedByUserID: item.UsernameOfAskedByUserID,
			ConFromItemOwner:        item.ConFromItemOwner,
			ConFromItemAsker:        item.ConFromItemAsker,
		})
	}
	return c.JSON(itemsResponse)
}

func (h *itemHandler) GetDonateItemsOfCurrentUser(c *fiber.Ctx) error {
	// Extract the token from the request headers
	token := c.Get("Authorization")

	// Check if the token is empty
	if token == "" {
		return errors.New("token is missing")
	}

	// Extract the user ID from the token
	userID, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	items, err := h.itemSer.GetDonateItemsOfCurrentUser(userID)
	if err != nil {
		return err
	}

	itemsResponse := make([]dtos.DonateItemsOfCurrentUserResponse, 0)
	for _, item := range items {
		itemsResponse = append(itemsResponse, dtos.DonateItemsOfCurrentUserResponse{
			ItemID:                  item.ItemID,
			UserID:                  item.UserID,
			Itemname:                item.Itemname,
			Description:             item.Description,
			ItemPic:                 item.ItemPic,
			OfferType:               item.OfferType,
			AskedByUserID:           item.AskedByUserID,
			AlreadyGave:             item.AlreadyGave,
			Username:                item.Username,
			UserPic:                 item.UserPic,
			UsernameOfAskedByUserID: item.UsernameOfAskedByUserID,
			ConFromItemOwner:        item.ConFromItemOwner,
			ConFromItemAsker:        item.ConFromItemAsker,
		})
	}
	return c.JSON(itemsResponse)
}

func (h *itemHandler) GetReceiveItemsOfCurrentUser(c *fiber.Ctx) error {
	// Extract the token from the request headers
	token := c.Get("Authorization")

	// Check if the token is empty
	if token == "" {
		return errors.New("token is missing")
	}

	// Extract the user ID from the token
	userID, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	items, err := h.itemSer.GetReceiveItemsOfCurrentUser(userID)
	if err != nil {
		return err
	}

	itemsResponse := make([]dtos.ReceiveItemsOfCurrentUserResponse, 0)
	for _, item := range items {
		itemsResponse = append(itemsResponse, dtos.ReceiveItemsOfCurrentUserResponse{
			ItemID:                  item.ItemID,
			UserID:                  item.UserID,
			Itemname:                item.Itemname,
			Description:             item.Description,
			ItemPic:                 item.ItemPic,
			OfferType:               item.OfferType,
			AskedByUserID:           item.AskedByUserID,
			AlreadyGave:             item.AlreadyGave,
			Username:                item.Username,
			UserPic:                 item.UserPic,
			UsernameOfAskedByUserID: item.UsernameOfAskedByUserID,
			ConFromItemOwner:        item.ConFromItemOwner,
			ConFromItemAsker:        item.ConFromItemAsker,
		})
	}
	return c.JSON(itemsResponse)
}

func (h *itemHandler) PostAddItem(c *fiber.Ctx) error {
	// Extract the token from the request headers
	token := c.Get("Authorization")

	// Check if the token is empty
	if token == "" {
		return errors.New("token is missing")
	}

	// Extract the user ID from the token
	userIDExtract, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	var request dtos.AddItemRequest
	if err := c.BodyParser(&request); err != nil {
		return err
	}

	// Check if a file is uploaded
	file, err := c.FormFile("file")
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "File not found")
	}

	// Call upload service to upload the file
	fileURL, err := h.uploadSer.UploadFile(file)
	if err != nil {
		return fiber.NewError(fiber.StatusInternalServerError, "Failed to upload file")
	}

	// Set the uploaded file URL in the registration request
	request.ItemPic = fileURL

	// Check if user_pic field is empty or nil
	if request.ItemPic == nil {
		return fiber.NewError(fiber.StatusBadRequest, "Item picture is required")
	}

	item, err := h.itemSer.PostAddItem(userIDExtract, request)
	if err != nil {
		return err
	}

	itemResponse := dtos.AddItemRequest{
		UserID:      item.UserID,
		Itemname:    item.Itemname,
		Description: item.Description,
		ItemPic:     item.ItemPic,
		OfferType:   item.OfferType,
	}

	return c.JSON(itemResponse)
}

func (h *itemHandler) DeleteItemByItemId(c *fiber.Ctx) error {
	itemIDReceive, err := strconv.Atoi(c.Params("ItemID"))
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "invalid itemID"})
	}

	err = h.itemSer.DeleteItemByItemId(itemIDReceive)
	if err != nil {
		if strings.Contains(err.Error(), "item not found") {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{"message": "item not found"})
		}
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"message": err.Error()}) //failed to delete project
	}

	return c.Status(fiber.StatusOK).JSON(fiber.Map{"message": "item deleted successfully"})
}

func (h *itemHandler) GetMarketPlace(c *fiber.Ctx) error {
	// Extract the token from the request headers
	token := c.Get("Authorization")

	// Check if the token is empty
	if token == "" {
		return errors.New("token is missing")
	}

	// Extract the user ID from the token
	userID, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	items, err := h.itemSer.GetMarketPlace(userID)
	if err != nil {
		return err
	}

	itemsResponse := make([]dtos.MarketPlaceResponse, 0)
	for _, item := range items {
		itemsResponse = append(itemsResponse, dtos.MarketPlaceResponse{
			ItemID:        item.ItemID,
			UserID:        item.UserID,
			Itemname:      item.Itemname,
			Description:   item.Description,
			ItemPic:       item.ItemPic,
			OfferType:     item.OfferType,
			AskedByUserID: item.AskedByUserID,
			AlreadyGave:   item.AlreadyGave,
			Username:      item.Username,
			UserPic:       item.UserPic,
		})
	}
	return c.JSON(itemsResponse)
}

func (h *itemHandler) GetDonateMarketPlace(c *fiber.Ctx) error {
	// Extract the token from the request headers
	token := c.Get("Authorization")

	// Check if the token is empty
	if token == "" {
		return errors.New("token is missing")
	}

	// Extract the user ID from the token
	userID, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	items, err := h.itemSer.GetDonateMarketPlace(userID)
	if err != nil {
		return err
	}

	itemsResponse := make([]dtos.DonateMarketPlaceResponse, 0)
	for _, item := range items {
		itemsResponse = append(itemsResponse, dtos.DonateMarketPlaceResponse{
			ItemID:        item.ItemID,
			UserID:        item.UserID,
			Itemname:      item.Itemname,
			Description:   item.Description,
			ItemPic:       item.ItemPic,
			OfferType:     item.OfferType,
			AskedByUserID: item.AskedByUserID,
			AlreadyGave:   item.AlreadyGave,
			Username:      item.Username,
			UserPic:       item.UserPic,
		})
	}
	return c.JSON(itemsResponse)
}

func (h *itemHandler) GetReceiveMarketPlace(c *fiber.Ctx) error {
	// Extract the token from the request headers
	token := c.Get("Authorization")

	// Check if the token is empty
	if token == "" {
		return errors.New("token is missing")
	}

	// Extract the user ID from the token
	userID, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	items, err := h.itemSer.GetReceiveMarketPlace(userID)
	if err != nil {
		return err
	}

	itemsResponse := make([]dtos.ReceiveMarketPlaceResponse, 0)
	for _, item := range items {
		itemsResponse = append(itemsResponse, dtos.ReceiveMarketPlaceResponse{
			ItemID:        item.ItemID,
			UserID:        item.UserID,
			Itemname:      item.Itemname,
			Description:   item.Description,
			ItemPic:       item.ItemPic,
			OfferType:     item.OfferType,
			AskedByUserID: item.AskedByUserID,
			AlreadyGave:   item.AlreadyGave,
			Username:      item.Username,
			UserPic:       item.UserPic,
		})
	}
	return c.JSON(itemsResponse)
}

//func (h *itemHandler) PutAskByItemId(c *fiber.Ctx) error {
//	itemIDReceive, err := strconv.Atoi(c.Params("ItemID"))
//	if err != nil {
//		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "invalid ItemID"})
//	}
//
//	askedByUserID, err := strconv.Atoi(c.Params("AskByUserID"))
//	if err != nil {
//		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "invalid UserID"})
//	}
//
//	_, err = h.itemSer.PutAskByItemId(itemIDReceive, askedByUserID)
//	if err != nil {
//		return err
//	}
//
//	return c.JSON(fiber.Map{"message": "Update asked_by_user_id & already_gave By ItemID & UserID successfully"})
//}

func (h *itemHandler) PutAskByItemIdAndPostAskMessage(c *fiber.Ctx) error {
	itemIDReceive, err := strconv.Atoi(c.Params("ItemID"))
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "invalid ItemID"})
	}

	askedByUserID, err := strconv.Atoi(c.Params("AskByUserID"))
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "invalid UserID"})
	}

	_, err = h.itemSer.PutAskByItemIdAndPostAskMessage(itemIDReceive, askedByUserID)
	if err != nil {
		return err
	}

	return c.JSON(fiber.Map{"message": "Update asked_by_user_id & already_gave By ItemID & UserID successfully and message posted"})
}

func (h *itemHandler) PutTransactionReady(c *fiber.Ctx) error {
	itemIDReceive, err := strconv.Atoi(c.Params("ItemID"))
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "invalid ItemID"})
	}

	// Extract the token from the request headers
	token := c.Get("Authorization")
	if token == "" {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{"error": "token is missing"})
	}

	userIDExtract, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	_, err = h.itemSer.PutTransactionReady(itemIDReceive, userIDExtract)
	if err != nil {
		return err
	}

	return c.JSON(fiber.Map{"message": "PutTransactionReady successfully"})
}

func (h *itemHandler) PutCompleteTransaction(c *fiber.Ctx) error {
	itemIDReceive, err := strconv.Atoi(c.Params("ItemID"))
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "invalid ItemID"})
	}

	// Extract the token from the request headers
	token := c.Get("Authorization")
	if token == "" {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{"error": "token is missing"})
	}

	userIDExtract, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	_, err = h.itemSer.PutCompleteTransaction(itemIDReceive, userIDExtract)
	if err != nil {
		return err
	}

	return c.JSON(fiber.Map{"message": "PutCompleteTransaction successfully"})
}
