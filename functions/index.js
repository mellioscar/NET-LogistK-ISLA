const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

exports.procesarRepartos = functions.firestore
  .document('repartos/{repartoId}')
  .onCreate(async (snap, context) => {
    const reparto = snap.data();
    
    // Actualizar estadísticas
    const statsRef = admin.firestore().collection('estadisticas').doc('repartos');
    await statsRef.update({
      total_repartos: admin.firestore.FieldValue.increment(1),
      ultima_actualizacion: admin.firestore.FieldValue.serverTimestamp()
    });
  });
