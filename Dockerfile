# Build stage
FROM golang:1.25-alpine AS builder

WORKDIR /app

# Install ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates tzdata

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source
COPY cmd/ ./cmd/
COPY internal/ ./internal/

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /weeklyroulette ./cmd/weeklyroulette

# Runtime stage
FROM alpine:3.19

# Install ca-certificates and timezone data
RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

# Copy binary from builder
COPY --from=builder /weeklyroulette .

# Create volume for database
RUN mkdir -p /data

# Set environment variables
ENV DATABASE_URL=/data/weeklyroulette.db

# Run
CMD ["./weeklyroulette"]
