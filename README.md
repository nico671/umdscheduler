# UMDScheduler Frontend

A Svelte app serving as a frontend for the UMDScheduler project, an application enabling UMD students to create better schedules, more easily.

## Features

- **Course Search**: Easily search for courses by department, course number, or keywords
- **Time Conflict Detection**: Automatic detection of scheduling conflicts
- **Schedule Optimization**: Algorithm to suggest optimal schedules based on preferences
- **Professor Ratings**: View professor ratings and reviews integrated from PlanetTerp, a review site for UMD classes and professors.

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm or yarn

### Installation

1. Clone the repository

   ```bash
   git clone https://github.com/yourusername/umdscheduler_frontend.git
   cd umdscheduler_frontend
   ```

2. Install dependencies

   ```bash
   npm install
   # or
   yarn install
   ```

3. Start the development server

   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Contributing

We welcome contributions from the community! Here's how you can help:

1. **Fork the repository**: Create your own copy of the project
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**: Implement your feature or bug fix
4. **Test your changes**: Ensure your changes don't break existing functionality
5. **Commit your changes**: `git commit -m "Description of your changes"`
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Submit a pull request**: Open a PR against the main repository

### Coding Standards

- Follow the existing code style
- Write meaningful commit messages
- Include comments in your code
- Write tests for new features

## Screenshots

![Example Image](screenshots/homescreen_base.png)
![Example Image](screenshots/generated_schedules.png)
![Example Image](screenshots/add_class_modal.png)

## Technologies Used

- [Svelte](https://svelte.dev/) - Frontend framework
- [TypeScript](https://www.typescriptlang.org/) - Type-safe JavaScript
- [Vite](https://vitejs.dev/) - Frontend build tool

## License

This project is licensed under the MIT License - see the LICENSE file for details.
