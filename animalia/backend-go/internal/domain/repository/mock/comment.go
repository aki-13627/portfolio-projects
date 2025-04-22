package mock

import (
	"github.com/aki-13627/animalia/backend-go/ent"
	"github.com/aki-13627/animalia/backend-go/internal/domain/repository"
	"github.com/google/uuid"
)

// MockCommentRepository is a mock implementation of the CommentRepository interface
type MockCommentRepository struct {
	CreateFunc func(userId uuid.UUID, postId uuid.UUID, content string) (*ent.Comment, error)
	DeleteFunc func(commentId string) error
}

// Ensure MockCommentRepository implements CommentRepository interface
var _ repository.CommentRepository = (*MockCommentRepository)(nil)

// Create calls the mocked CreateFunc
func (m *MockCommentRepository) Create(userId uuid.UUID, postId uuid.UUID, content string) (*ent.Comment, error) {
	return m.CreateFunc(userId, postId, content)
}

// Delete calls the mocked DeleteFunc
func (m *MockCommentRepository) Delete(commentId string) error {
	return m.DeleteFunc(commentId)
}
