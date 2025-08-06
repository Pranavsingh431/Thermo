# Contributing to Thermal Inspection System

Thank you for your interest in contributing to the Thermal Inspection System! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/yourusername/thermal-inspection-system.git
   cd thermal-inspection-system
   ```
3. **Set up the development environment**:
   ```bash
   # Backend
   cd backend
   pip install -r requirements-dev.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

## 🔧 Development Setup

### Backend Development
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm start
```

### Running Tests
```bash
# Backend tests
cd backend
python -m pytest

# API testing
python test_api.py
```

## 📝 Code Style

### Python (Backend)
- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to functions and classes
- Maximum line length: 100 characters

### JavaScript/React (Frontend)
- Use ES6+ features
- Follow React best practices
- Use meaningful component and variable names
- Add JSDoc comments for complex functions

### General Guidelines
- Write descriptive commit messages
- Add comments for complex logic
- Ensure code is tested before submitting
- Update documentation when needed

## 🐛 Bug Reports

When filing bug reports, please include:

1. **Environment details**: OS, Python version, Node.js version
2. **Steps to reproduce**: Clear, numbered steps
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Error messages**: Include full stack traces
6. **Screenshots**: If applicable

## 💡 Feature Requests

For feature requests, please provide:

1. **Use case**: Why is this feature needed?
2. **Proposed solution**: How should it work?
3. **Alternatives considered**: Other approaches you've thought about
4. **Additional context**: Any other relevant information

## 🔀 Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**:
   - Write clean, documented code
   - Add tests for new functionality
   - Ensure all tests pass

3. **Commit your changes**:
   ```bash
   git commit -m "Add amazing feature: brief description"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature
   ```

5. **Create a Pull Request**:
   - Use a descriptive title
   - Explain what changes you made
   - Reference any related issues
   - Include screenshots if applicable

## 🧪 Testing Guidelines

### Backend Testing
- Write unit tests for new functions
- Test API endpoints thoroughly
- Include edge cases and error conditions
- Maintain test coverage above 80%

### Frontend Testing
- Test React components
- Test user interactions
- Test API integration
- Include accessibility testing

## 📚 Documentation

When contributing, please:

- Update README.md if needed
- Add inline code comments
- Update API documentation
- Include examples for new features

## 🚫 What Not to Include

Please avoid including:

- Sensitive configuration files
- Database files with real data
- Large binary files
- Personal API keys or secrets
- Temporary files or build artifacts

## 📞 Getting Help

If you need help:

1. Check existing issues and discussions
2. Read the documentation thoroughly
3. Ask questions in GitHub Discussions
4. Contact maintainers for complex issues

## 🎯 Areas for Contribution

We welcome contributions in these areas:

- **AI/ML improvements**: Better models, accuracy improvements
- **Frontend enhancements**: UI/UX improvements, new features
- **Testing**: More comprehensive test coverage
- **Documentation**: Better guides, tutorials, examples
- **Performance**: Speed and efficiency improvements
- **Security**: Security audits and improvements

## 📋 Code Review Process

All submissions require code review:

1. **Automated checks**: CI/CD pipeline must pass
2. **Peer review**: At least one maintainer review
3. **Testing**: All tests must pass
4. **Documentation**: Updates must be included

## ⚖️ License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to the Thermal Inspection System! 🔥 