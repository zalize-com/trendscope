window.onload = () => {
  try {
    SwaggerUIBundle({
      url: "docs/api/openapi.yaml",
      dom_id: "#ui",
      deepLinking: true,
      tryItOutEnabled: true,
      defaultModelsExpandDepth: 1,
      docExpansion: "list"
    });
  } catch(e){ document.getElementById("err").textContent = "swagger-ui failed to load — " + e.message; }
};
