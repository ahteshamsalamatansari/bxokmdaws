const express = require('express');
const router = express.Router();

router.post('/register', (req, res) => {
  res.status(501).json({ msg: 'Not implemented' });
});

module.exports = router;