package service

import (
	"fmt"
	"github.com/gofiber/fiber/v2"
	"log"
	"needful/internal/dtos"
	"needful/internal/entities"
	"needful/internal/repository"
	"needful/internal/utils/v"
	"strings"
)

type itemService struct {
	itemRepo repository.ItemRepository
}

func NewItemService(itemRepo repository.ItemRepository) itemService {
	return itemService{itemRepo: itemRepo}
}

func (s itemService) GetItems() ([]entities.Item, error) {
	items, err := s.itemRepo.GetAllItem()
	if err != nil {
		log.Println(err)
		return nil, err
	}

	itemResponses := []entities.Item{}
	for _, item := range items {
		itemResponse := entities.Item{
			ItemID:           item.ItemID,
			UserID:           item.UserID,
			Itemname:         item.Itemname,
			Description:      item.Description,
			ItemPic:          item.ItemPic,
			OfferType:        item.OfferType,
			AskedByUserID:    item.AskedByUserID,
			AlreadyGave:      item.AlreadyGave,
			ConFromItemOwner: item.ConFromItemOwner,
			ConFromItemAsker: item.ConFromItemAsker,
		}
		itemResponses = append(itemResponses, itemResponse)
	}
	return itemResponses, nil
}

func (s itemService) GetItemByUserId(userid int) ([]entities.Item, error) {
	items, err := s.itemRepo.GetItemByUserId(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	itemResponses := []entities.Item{}
	for _, item := range items {
		itemResponse := entities.Item{
			ItemID:           item.ItemID,
			UserID:           item.UserID,
			Itemname:         item.Itemname,
			Description:      item.Description,
			ItemPic:          item.ItemPic,
			OfferType:        item.OfferType,
			AskedByUserID:    item.AskedByUserID,
			AlreadyGave:      item.AlreadyGave,
			ConFromItemOwner: item.ConFromItemOwner,
			ConFromItemAsker: item.ConFromItemAsker,
		}
		itemResponses = append(itemResponses, itemResponse)
	}
	return itemResponses, nil
}

func (s itemService) GetItemByItemId(itemid int) (*entities.Item, error) {
	item, err := s.itemRepo.GetItemByItemId(itemid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	if *item == (entities.Item{}) {
		return nil, fiber.NewError(fiber.StatusNotFound, "item doesn't exist")
	}

	itemResponse := entities.Item{
		ItemID:           item.ItemID,
		UserID:           item.UserID,
		Itemname:         item.Itemname,
		Description:      item.Description,
		ItemPic:          item.ItemPic,
		OfferType:        item.OfferType,
		AskedByUserID:    item.AskedByUserID,
		AlreadyGave:      item.AlreadyGave,
		ConFromItemOwner: item.ConFromItemOwner,
		ConFromItemAsker: item.ConFromItemAsker,
	}
	return &itemResponse, nil
}

////////////////////////////////////////////////////////////////////////////////////////////////////

func (s itemService) GetItemDetailsByItemId(itemid int) (*entities.Item, error) {
	item, err := s.itemRepo.GetItemDetailsByItemId(itemid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	if *item == (entities.Item{}) {
		return nil, fiber.NewError(fiber.StatusNotFound, "item doesn't exist")
	}

	itemResponse := entities.Item{
		ItemID:           item.ItemID,
		UserID:           item.UserID,
		Itemname:         item.Itemname,
		Description:      item.Description,
		ItemPic:          item.ItemPic,
		OfferType:        item.OfferType,
		AskedByUserID:    item.AskedByUserID,
		AlreadyGave:      item.AlreadyGave,
		ConFromItemOwner: item.ConFromItemOwner,
		ConFromItemAsker: item.ConFromItemAsker,
	}
	return &itemResponse, nil
}

////////////////////////////////////////////////////////////////////////////////////////////////////

func (s itemService) GetItemsOfCurrentUser(userid int) ([]entities.ItemsOfCurrentUserResponse, error) {
	items, err := s.itemRepo.GetAllItemOfCurrentUser(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	itemsResponse := []entities.ItemsOfCurrentUserResponse{}
	for _, item := range items {
		itemResponse := entities.ItemsOfCurrentUserResponse{
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
		}
		itemsResponse = append(itemsResponse, itemResponse)
	}
	return itemsResponse, nil
}

func (s itemService) GetDonateItemsOfCurrentUser(userid int) ([]entities.DonateItemsOfCurrentUserResponse, error) {
	items, err := s.itemRepo.GetDonateItemsOfCurrentUser(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	itemsResponse := []entities.DonateItemsOfCurrentUserResponse{}
	for _, item := range items {
		itemResponse := entities.DonateItemsOfCurrentUserResponse{
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
		}
		itemsResponse = append(itemsResponse, itemResponse)
	}
	return itemsResponse, nil
}

func (s itemService) GetReceiveItemsOfCurrentUser(userid int) ([]entities.ReceiveItemsOfCurrentUserResponse, error) {
	items, err := s.itemRepo.GetReceiveItemsOfCurrentUser(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	itemsResponse := []entities.ReceiveItemsOfCurrentUserResponse{}
	for _, item := range items {
		itemResponse := entities.ReceiveItemsOfCurrentUserResponse{
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
		}
		itemsResponse = append(itemsResponse, itemResponse)
	}
	return itemsResponse, nil
}

func (s itemService) PostAddItem(userID int, req dtos.AddItemRequest) (*entities.Item, error) {
	item := &entities.Item{
		UserID:      v.UintPtr(userID),
		Itemname:    req.Itemname,
		Description: req.Description,
		ItemPic:     req.ItemPic,
		OfferType:   req.OfferType,
	}

	err := s.itemRepo.PostAddItem(item)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	return item, nil
}

func (s itemService) DeleteItemByItemId(itemID int) error {
	_, err := s.GetItemByItemId(itemID)
	if err != nil {
		if strings.Contains(err.Error(), "item doesn't exist") {
			return fiber.NewError(fiber.StatusNotFound, "item not found")
		}
		return err
	}

	err = s.itemRepo.DeleteItemByItemId(itemID)
	if err != nil {
		return err
	}

	return nil
}

func (s itemService) GetMarketPlace(userid int) ([]entities.MarketPlaceResponse, error) {
	items, err := s.itemRepo.GetMarketPlace(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	itemsResponse := []entities.MarketPlaceResponse{}
	for _, item := range items {
		itemResponse := entities.MarketPlaceResponse{
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
		}
		itemsResponse = append(itemsResponse, itemResponse)
	}
	return itemsResponse, nil
}

func (s itemService) GetDonateMarketPlace(userid int) ([]entities.DonateMarketPlaceResponse, error) {
	items, err := s.itemRepo.GetDonateMarketPlace(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	itemsResponse := []entities.DonateMarketPlaceResponse{}
	for _, item := range items {
		itemResponse := entities.DonateMarketPlaceResponse{
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
		}
		itemsResponse = append(itemsResponse, itemResponse)
	}
	return itemsResponse, nil
}

func (s itemService) GetReceiveMarketPlace(userid int) ([]entities.ReceiveMarketPlaceResponse, error) {
	items, err := s.itemRepo.GetReceiveMarketPlace(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	itemsResponse := []entities.ReceiveMarketPlaceResponse{}
	for _, item := range items {
		itemResponse := entities.ReceiveMarketPlaceResponse{
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
		}
		itemsResponse = append(itemsResponse, itemResponse)
	}
	return itemsResponse, nil
}

//func (s itemService) PutAskByItemId(itemID, askerUserID int) (*entities.Item, error) {
//	item, err := s.itemRepo.GetItemByItemId(itemID)
//	if err != nil {
//		return nil, err
//	}
//
//	gave := false
//	item.AlreadyGave = &gave
//
//	item.AskedByUserID = v.UintPtr(askerUserID)
//
//	err = s.itemRepo.PutAskByItemId(item)
//	if err != nil {
//		return nil, err
//	}
//
//	return item, nil
//}

func (s itemService) PutAskByItemIdAndPostAskMessage(itemID, askerUserID int) (*entities.Item, error) {
	item, err := s.itemRepo.GetItemByItemId(itemID)
	if err != nil {
		return nil, err
	}

	gave := false
	item.AlreadyGave = &gave
	item.AskedByUserID = v.UintPtr(askerUserID)

	err = s.itemRepo.PutAskByItemId(item)
	if err != nil {
		return nil, err
	}

	// Determine the preposition based on the OfferType
	var preposition string
	var askMSGType string
	if *item.OfferType == "Receive" {
		askMSGType = "Donate"
		preposition = "for"
	} else if *item.OfferType == "Donate" {
		askMSGType = "Receive"
		preposition = "from"
	} else {
		preposition = "with"
	}

	// Create the message text
	messageText := fmt.Sprintf("Hi! I want to %s %s %s you", askMSGType, *item.Itemname, preposition)

	message := &entities.Message{
		SenderUserID:   v.UintPtr(askerUserID),
		ReceiverUserID: item.UserID,
		MsgText:        &messageText,
	}

	err = s.itemRepo.PostAskMessage(message)
	if err != nil {
		return nil, err
	}

	return item, nil
}

func (s itemService) PutTransactionReady(itemid, userid int) (*entities.Item, error) {
	item, err := s.itemRepo.GetItemByItemId(itemid)
	if err != nil {
		return nil, err
	}

	if item.AskedByUserID != nil && *item.AskedByUserID == uint(userid) {
		T1 := false
		item.ConFromItemAsker = &T1
	} else {
		T1 := false
		item.ConFromItemOwner = &T1
	}

	err = s.itemRepo.PutTransactionReady(item)
	if err != nil {
		return nil, err
	}

	return item, nil
}

func (s itemService) PutCompleteTransaction(itemid, userid int) (*entities.Item, error) {
	item, err := s.itemRepo.GetItemByItemId(itemid)
	if err != nil {
		return nil, err
	}

	T1 := true

	if item.AskedByUserID != nil && *item.AskedByUserID == uint(userid) {
		item.ConFromItemAsker = &T1
	} else {
		item.ConFromItemOwner = &T1
	}

	// Check if both confirmations are true
	if item.ConFromItemOwner != nil && *item.ConFromItemOwner &&
		item.ConFromItemAsker != nil && *item.ConFromItemAsker {
		item.AlreadyGave = &T1
	}

	err = s.itemRepo.PutCompleteTransaction(item)
	if err != nil {
		return nil, err
	}

	return item, nil
}
