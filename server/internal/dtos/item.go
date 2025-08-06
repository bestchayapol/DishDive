package dtos

type ItemDataResponse struct {
	ItemID           *uint   `json:"item_id" validate:"required"`
	UserID           *uint   `json:"user_id" validate:"required"`
	Itemname         *string `json:"itemname" validate:"required"`
	Description      *string `json:"description" validate:"required"`
	ItemPic          *string `json:"item_pic" validate:"required"`
	OfferType        *string `json:"offer_type" validate:"required"`
	AskedByUserID    *uint   `json:"asked_by_user_id" validate:"required"`
	AlreadyGave      *bool   `json:"already_gave" validate:"required"`
	ConFromItemOwner *bool   `json:"con_from_item_owner" validate:"required"`
	ConFromItemAsker *bool   `json:"con_from_item_asker" validate:"required"`
}

type ItemDataByUserIdResponse struct {
	ItemID           *uint   `json:"item_id" validate:"required"`
	UserID           *uint   `json:"user_id" validate:"required"`
	Itemname         *string `json:"itemname" validate:"required"`
	Description      *string `json:"description" validate:"required"`
	ItemPic          *string `json:"item_pic" validate:"required"`
	OfferType        *string `json:"offer_type" validate:"required"`
	AskedByUserID    *uint   `json:"asked_by_user_id" validate:"required"`
	AlreadyGave      *bool   `json:"already_gave" validate:"required"`
	ConFromItemOwner *bool   `json:"con_from_item_owner" validate:"required"`
	ConFromItemAsker *bool   `json:"con_from_item_asker" validate:"required"`
}

type ItemDataByItemIdResponse struct {
	ItemID           *uint   `json:"item_id" validate:"required"`
	UserID           *uint   `json:"user_id" validate:"required"`
	Itemname         *string `json:"itemname" validate:"required"`
	Description      *string `json:"description" validate:"required"`
	ItemPic          *string `json:"item_pic" validate:"required"`
	OfferType        *string `json:"offer_type" validate:"required"`
	AskedByUserID    *uint   `json:"asked_by_user_id" validate:"required"`
	AlreadyGave      *bool   `json:"already_gave" validate:"required"`
	ConFromItemOwner *bool   `json:"con_from_item_owner" validate:"required"`
	ConFromItemAsker *bool   `json:"con_from_item_asker" validate:"required"`
}

///////////////////////////////////////////////////

type ItemDetailsByItemIdResponse struct {
	ItemID           *uint   `json:"item_id" validate:"required"`
	UserID           *uint   `json:"user_id" validate:"required"`
	Itemname         *string `json:"itemname" validate:"required"`
	Description      *string `json:"description" validate:"required"`
	ItemPic          *string `json:"item_pic" validate:"required"`
	OfferType        *string `json:"offer_type" validate:"required"`
	AskedByUserID    *uint   `json:"asked_by_user_id" validate:"required"`
	AlreadyGave      *bool   `json:"already_gave" validate:"required"`
	ConFromItemOwner *bool   `json:"con_from_item_owner" validate:"required"`
	ConFromItemAsker *bool   `json:"con_from_item_asker" validate:"required"`
}

///////////////////////////////////////////////////

type ItemsOfCurrentUserResponse struct {
	ItemID                  *uint   `json:"item_id" validate:"required"`
	UserID                  *uint   `json:"user_id" validate:"required"`
	Itemname                *string `json:"itemname" validate:"required"`
	Description             *string `json:"description" validate:"required"`
	ItemPic                 *string `json:"item_pic" validate:"required"`
	OfferType               *string `json:"offer_type" validate:"required"`
	AskedByUserID           *uint   `json:"asked_by_user_id" validate:"required"`
	AlreadyGave             *bool   `json:"already_gave" validate:"required"`
	Username                *string `json:"username" validate:"required"`
	UserPic                 *string `json:"user_pic" validate:"required"`
	UsernameOfAskedByUserID *string `json:"username_asked_by_user_id" validate:"required"`
	ConFromItemOwner        *bool   `json:"con_from_item_owner" validate:"required"`
	ConFromItemAsker        *bool   `json:"con_from_item_asker" validate:"required"`
}

type DonateItemsOfCurrentUserResponse struct {
	ItemID                  *uint   `json:"item_id" validate:"required"`
	UserID                  *uint   `json:"user_id" validate:"required"`
	Itemname                *string `json:"itemname" validate:"required"`
	Description             *string `json:"description" validate:"required"`
	ItemPic                 *string `json:"item_pic" validate:"required"`
	OfferType               *string `json:"offer_type" validate:"required"`
	AskedByUserID           *uint   `json:"asked_by_user_id" validate:"required"`
	AlreadyGave             *bool   `json:"already_gave" validate:"required"`
	Username                *string `json:"username" validate:"required"`
	UserPic                 *string `json:"user_pic" validate:"required"`
	UsernameOfAskedByUserID *string `json:"username_asked_by_user_id" validate:"required"`
	ConFromItemOwner        *bool   `json:"con_from_item_owner" validate:"required"`
	ConFromItemAsker        *bool   `json:"con_from_item_asker" validate:"required"`
}

type ReceiveItemsOfCurrentUserResponse struct {
	ItemID                  *uint   `json:"item_id" validate:"required"`
	UserID                  *uint   `json:"user_id" validate:"required"`
	Itemname                *string `json:"itemname" validate:"required"`
	Description             *string `json:"description" validate:"required"`
	ItemPic                 *string `json:"item_pic" validate:"required"`
	OfferType               *string `json:"offer_type" validate:"required"`
	AskedByUserID           *uint   `json:"asked_by_user_id" validate:"required"`
	AlreadyGave             *bool   `json:"already_gave" validate:"required"`
	Username                *string `json:"username" validate:"required"`
	UserPic                 *string `json:"user_pic" validate:"required"`
	UsernameOfAskedByUserID *string `json:"username_asked_by_user_id" validate:"required"`
	ConFromItemOwner        *bool   `json:"con_from_item_owner" validate:"required"`
	ConFromItemAsker        *bool   `json:"con_from_item_asker" validate:"required"`
}

type AddItemRequest struct {
	UserID      *uint   `json:"user_id" validate:"required"`
	Itemname    *string `json:"itemname" validate:"required"`
	Description *string `json:"description" validate:"required"`
	ItemPic     *string `json:"item_pic" validate:"required"`
	OfferType   *string `json:"offer_type" validate:"required"`
}

type MarketPlaceResponse struct {
	ItemID        *uint   `json:"item_id" validate:"required"`
	UserID        *uint   `json:"user_id" validate:"required"`
	Itemname      *string `json:"itemname" validate:"required"`
	Description   *string `json:"description" validate:"required"`
	ItemPic       *string `json:"item_pic" validate:"required"`
	OfferType     *string `json:"offer_type" validate:"required"`
	AskedByUserID *uint   `json:"asked_by_user_id" validate:"required"`
	AlreadyGave   *bool   `json:"already_gave" validate:"required"`
	Username      *string `json:"username" validate:"required"`
	UserPic       *string `json:"user_pic" validate:"required"`
}

type DonateMarketPlaceResponse struct {
	ItemID        *uint   `json:"item_id" validate:"required"`
	UserID        *uint   `json:"user_id" validate:"required"`
	Itemname      *string `json:"itemname" validate:"required"`
	Description   *string `json:"description" validate:"required"`
	ItemPic       *string `json:"item_pic" validate:"required"`
	OfferType     *string `json:"offer_type" validate:"required"`
	AskedByUserID *uint   `json:"asked_by_user_id" validate:"required"`
	AlreadyGave   *bool   `json:"already_gave" validate:"required"`
	Username      *string `json:"username" validate:"required"`
	UserPic       *string `json:"user_pic" validate:"required"`
}

type ReceiveMarketPlaceResponse struct {
	ItemID        *uint   `json:"item_id" validate:"required"`
	UserID        *uint   `json:"user_id" validate:"required"`
	Itemname      *string `json:"itemname" validate:"required"`
	Description   *string `json:"description" validate:"required"`
	ItemPic       *string `json:"item_pic" validate:"required"`
	OfferType     *string `json:"offer_type" validate:"required"`
	AskedByUserID *uint   `json:"asked_by_user_id" validate:"required"`
	AlreadyGave   *bool   `json:"already_gave" validate:"required"`
	Username      *string `json:"username" validate:"required"`
	UserPic       *string `json:"user_pic" validate:"required"`
}
