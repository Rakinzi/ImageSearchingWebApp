//e11012a097b84c87b39adfcd45c6448f
//const uri = "mongodb+srv://tmotsi14:tapiwa@cluster0.otf3c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"; // Replace with your MongoDB connection string
import express from 'express';
import { MongoClient } from 'mongodb';
import Clarifai from 'clarifai';
import cors from 'cors';

const app = express();
app.use(express.json());
app.use(cors());

// Clarifai initialization with API Key
const clarifaiApp = new Clarifai.App({
  apiKey: 'e11012a097b84c87b39adfcd45c6448f',
});

// MongoDB connection
const mongoUri = 'mongodb+srv://tmotsi14:tapiwa@cluster0.otf3c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0';
const dbName = 'file_upload_db';
let db;
(async () => {
    try {
      const client = await MongoClient.connect(mongoUri);
      console.log('Connected to MongoDB');
      db = client.db(dbName);
    } catch (err) {
      console.error('MongoDB connection error:', err);
    }
  })();

// API to handle file upload data and Clarifai analysis
app.post('/upload', async (req, res) => {
  const { fileUrl, fileName } = req.body;

  try {
    // Perform Clarifai analysis
    const clarifaiResponse = await clarifaiApp.models.predict(Clarifai.GENERAL_MODEL, fileUrl);
    const clarifaiData = clarifaiResponse.outputs[0].data.concepts;

    // Store metadata in MongoDB
    const fileMetadata = {
      name: fileName,
      url: fileUrl,
      analysis: clarifaiData,
      uploadedAt: new Date(),
    };

    const collection = db.collection('files');
    await collection.insertOne(fileMetadata);

    res.status(200).json({ success: true, analysis: clarifaiData });
  } catch (error) {
    console.error('Error processing file:', error);
    res.status(500).json({ success: false, message: 'Error processing file' });
  }
});
// Existing imports and MongoDB setup code...

// API to retrieve all files from MongoDB
app.get('/files', async (req, res) => {
    try {
      const collection = db.collection('files');
      const files = await collection.find({}).toArray();
      res.status(200).json(files);
    } catch (error) {
      console.error('Error fetching files:', error);
      res.status(500).json({ success: false, message: 'Error fetching files' });
    }
  });
  
  // API to retrieve a specific file by ID
  app.get('/files/:id', async (req, res) => {
    const { id } = req.params;
  
    try {
      const collection = db.collection('files');
      const file = await collection.findOne({ _id: new MongoClient.ObjectId(id) }); // Fetch file by ID
      if (!file) {
        return res.status(404).json({ success: false, message: 'File not found' });
      }
      res.status(200).json(file); // Send file as response
    } catch (error) {
      console.error('Error fetching file:', error);
      res.status(500).json({ success: false, message: 'Error fetching file' });
    }
  });

  app.get('/search', async (req, res) => {
    console.log('Search request received:', req.query);
    const { query } = req.query; // Extract query parameter from request

    if (!query) {
        return res.status(400).json({ success: false, message: 'Query parameter is required' });
    }

    try {
        const collection = db.collection('files');
        const results = await collection.find({
            analysis: {
                $elemMatch: {
                    name: { $regex: query, $options: 'i' }, // Case-insensitive regex search
                },
            },
        }).toArray();

        res.status(200).json(results);
    } catch (error) {
        console.error('Error searching files:', error);
        res.status(500).json({ success: false, message: 'Error searching files' });
    }
});

app.get('/suggestions', async (req, res) => {
    const { query } = req.query;

    if (!query) {
        return res.status(400).json({ success: false, message: 'Query parameter is required' });
    }

    try {
        const collection = db.collection('files');
        const results = await collection.distinct('analysis.name', {
            name: { $regex: query, $options: 'i' }, // Assuming 'analysis.name' is the field to search
        });

        res.status(200).json(results);
    } catch (error) {
        console.error('Error fetching suggestions:', error);
        res.status(500).json({ success: false, message: 'Error fetching suggestions' });
    }
});
  // Start the server
  app.listen(5000, () => {
    console.log('Server running on port 5000');
  });
  
/*add file retrival here*/
/* file data is like this 
{"_id":{"$oid":"66f31c05867185daaa34e81d"},"name":"Screenshot from 2024-09-19 21-50-13.png","url":"https://firebasestorage.googleapis.com/v0/b/g-drive-one.appspot.com/o/uploads%2FScreenshot%20from%202024-09-19%2021-50-13.png?alt=media&token=330b0401-feb9-490f-82d7-4eceaef928a3","analysis":[{"id":"ai_RmpTltl9","name":"stripe","value":{"$numberDouble":"0.9914262"},"app_id":"main"},{"id":"ai_vkQnVcpx","name":"navigation","value":{"$numberDouble":"0.99040854"},"app_id":"main"},{"id":"ai_15WdDpTW","name":"site","value":{"$numberDouble":"0.98930407"},"app_id":"main"},{"id":"ai_MnBdTFRf","name":"template","value":{"$numberDouble":"0.98097163"},"app_id":"main"},{"id":"ai_WCsfx0Ft","name":"World Wide Web","value":{"$numberDouble":"0.9784868"},"app_id":"main"},{"id":"ai_lxhDkMj0","name":"interface","value":{"$numberDouble":"0.9745749"},"app_id":"main"},{"id":"ai_tDL2Z0CD","name":"user","value":{"$numberDouble":"0.97175443"},"app_id":"main"},{"id":"ai_jsqHqS3p","name":"menu (food)","value":{"$numberDouble":"0.96591824"},"app_id":"main"},{"id":"ai_W10gz9w2","name":"login","value":{"$numberDouble":"0.96323836"},"app_id":"main"},{"id":"ai_hSgFm2Bt","name":"set","value":{"$numberDouble":"0.9554591"},"app_id":"main"},{"id":"ai_M7TvgbrL","name":"page","value":{"$numberDouble":"0.95106626"},"app_id":"main"},{"id":"ai_bqrpPDMX","name":"restaurant check","value":{"$numberDouble":"0.947009"},"app_id":"main"},{"id":"ai_m5Kbh58K","name":"form","value":{"$numberDouble":"0.9452732"},"app_id":"main"},{"id":"ai_Grf0d5hc","name":"download","value":{"$numberDouble":"0.9434767"},"app_id":"main"},{"id":"ai_ZqnMpL6s","name":"register","value":{"$numberDouble":"0.9284085"},"app_id":"main"},{"id":"ai_5NvRrw97","name":"facts","value":{"$numberDouble":"0.92251104"},"app_id":"main"},{"id":"ai_5wWgL0wP","name":"label","value":{"$numberDouble":"0.9188319"},"app_id":"main"},{"id":"ai_xTlJcHph","name":"skidder","value":{"$numberDouble":"0.9082407"},"app_id":"main"},{"id":"ai_w6DQ70Hq","name":"heading","value":{"$numberDouble":"0.9075009"},"app_id":"main"},{"id":"ai_gq6npDVT","name":"browse","value":{"$numberDouble":"0.9059242"},"app_id":"main"}],"uploadedAt":{"$date":{"$numberLong":"1727208453709"}}}
*/