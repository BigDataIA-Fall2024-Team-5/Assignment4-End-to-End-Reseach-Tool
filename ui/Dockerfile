# Frontend Dockerfile

# Use a Node.js image as a parent image
FROM node:20

# Install pnpm globally
RUN npm install -g pnpm

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and pnpm-lock.yaml files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm i

# Copy the rest of the application code
COPY . /app

# Expose the port the app runs on (usually 3000 for Next.js apps)
EXPOSE 3000

# Run the application
CMD ["pnpm", "dev"]
