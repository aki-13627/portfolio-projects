package schema

import (
	"time"

	"entgo.io/ent"
	"entgo.io/ent/schema/edge"
	"entgo.io/ent/schema/field"
	"entgo.io/ent/schema/index"
	"github.com/google/uuid"
)

// FollowRelation holds the schema definition for the FollowRelation entity.
type FollowRelation struct {
	ent.Schema
}

// Fields of the FollowRelation.
func (FollowRelation) Fields() []ent.Field {
	return []ent.Field{
		field.UUID("id", uuid.UUID{}).Default(uuid.New).Unique(),
		field.Time("created_at").Default(time.Now),
	}
}

// Edges of the FollowRelation.
func (FollowRelation) Edges() []ent.Edge {
	return []ent.Edge{
		edge.From("from", User.Type).Ref("following").Unique().Required(),
		edge.From("to", User.Type).Ref("followers").Unique().Required(),
	}
}

func (FollowRelation) Indexes() []ent.Index {
	return []ent.Index{
		index.Edges("from", "to").Unique(),
	}
}
