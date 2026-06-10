const Post = require('../models/Post');

exports.getPosts = async (req, res, next) => {
  try {
    const posts = await Post.find().populate('user', 'username email');
    res.status(200).json({ success: true, count: posts.length, data: posts });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
};

// @desc    Create new post
// @route   POST /api/posts
// @access  Private
exports.createPost = async (req, res, next) => {
  try {
    // Add user ID to request body
    req.body.user = req.user.id;

    const post = await Post.create(req.body);
    res.status(201).json({ success: true, data: post });
  } catch (err) {
    res.status(400).json({ success: false, error: err.message });
  }
};