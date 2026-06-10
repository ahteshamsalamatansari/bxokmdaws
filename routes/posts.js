const express = require('express');
const { getPosts, createPost, getPost } = require('../controllers/postController');
const { protect } = require('../middleware/auth');
const router = express.Router();

router.route('/')
  .get(getPosts)
  .post(protect, createPost);

router.route('/:id')
  .get(getPost);

module.exports = router;