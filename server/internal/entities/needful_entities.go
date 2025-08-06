package entities

type User struct {
	UserID    *uint `gorm:"primaryKey;autoIncrement"`
	Username  *string
	Password  *string
	Email     *string
	Firstname *string
	Lastname  *string
	PhoneNum  *string
	UserPic   *string
}

type Item struct {
	ItemID           *uint `gorm:"primaryKey;autoIncrement"`
	UserID           *uint `gorm:"not null"`
	Itemname         *string
	Description      *string
	ItemPic          *string
	OfferType        *string
	AskedByUserID    *uint
	AlreadyGave      *bool
	ConFromItemOwner *bool
	ConFromItemAsker *bool
	///////////////////////////////////////////////
	User User `gorm:"foreignKey:UserID"`
	//////////////////////////////////////////////

}

type Message struct {
	MsgID          *uint `gorm:"primaryKey;autoIncrement"`
	SenderUserID   *uint `gorm:"not null;"`
	ReceiverUserID *uint `gorm:"not null;"`
	MsgText        *string
}

type ItemsOfCurrentUserResponse struct {
	ItemID                  *uint
	UserID                  *uint
	Itemname                *string
	Description             *string
	ItemPic                 *string
	OfferType               *string
	AskedByUserID           *uint
	AlreadyGave             *bool
	Username                *string
	UserPic                 *string
	UsernameOfAskedByUserID *string
	ConFromItemOwner        *bool
	ConFromItemAsker        *bool
}

type DonateItemsOfCurrentUserResponse struct {
	ItemID                  *uint
	UserID                  *uint
	Itemname                *string
	Description             *string
	ItemPic                 *string
	OfferType               *string
	AskedByUserID           *uint
	AlreadyGave             *bool
	Username                *string
	UserPic                 *string
	UsernameOfAskedByUserID *string
	ConFromItemOwner        *bool
	ConFromItemAsker        *bool
}

type ReceiveItemsOfCurrentUserResponse struct {
	ItemID                  *uint
	UserID                  *uint
	Itemname                *string
	Description             *string
	ItemPic                 *string
	OfferType               *string
	AskedByUserID           *uint
	AlreadyGave             *bool
	Username                *string
	UserPic                 *string
	UsernameOfAskedByUserID *string
	ConFromItemOwner        *bool
	ConFromItemAsker        *bool
}

type MarketPlaceResponse struct {
	ItemID        *uint
	UserID        *uint
	Itemname      *string
	Description   *string
	ItemPic       *string
	OfferType     *string
	AskedByUserID *uint
	AlreadyGave   *bool
	Username      *string
	UserPic       *string
}

type DonateMarketPlaceResponse struct {
	ItemID        *uint
	UserID        *uint
	Itemname      *string
	Description   *string
	ItemPic       *string
	OfferType     *string
	AskedByUserID *uint
	AlreadyGave   *bool
	Username      *string
	UserPic       *string
}

type ReceiveMarketPlaceResponse struct {
	ItemID        *uint
	UserID        *uint
	Itemname      *string
	Description   *string
	ItemPic       *string
	OfferType     *string
	AskedByUserID *uint
	AlreadyGave   *bool
	Username      *string
	UserPic       *string
}

type MessagePageOfCurrentUserResponse struct {
	UserID         *uint
	Username       *string
	Firstname      *string
	Lastname       *string
	UserPic        *string
	MsgID          *uint
	SenderUserID   *uint
	ReceiverUserID *uint
	MsgText        *string
}

type ConversationOfCurrentUserByOtherIDResponse struct {
	UserID         *uint
	Username       *string
	Firstname      *string
	Lastname       *string
	UserPic        *string
	MsgID          *uint
	SenderUserID   *uint
	ReceiverUserID *uint
	MsgText        *string
}
