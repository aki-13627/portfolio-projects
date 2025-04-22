package repository

import (
	"github.com/aki-13627/animalia/backend-go/ent"
)

type UserRepository interface {
	Create(name, email string) (*ent.User, error)
	ExistsEmail(email string) (bool, error)
	FindByEmail(email string) (*ent.User, error)
	GetById(id string) (*ent.User, error)
	Update(id string, name string, description string, newImageKey string) error
	Follow(toId string, fromId string) error
	Unfollow(toId string, fromId string) error
}
