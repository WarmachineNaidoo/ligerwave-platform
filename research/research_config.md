# Research Agent Configuration — AttnValue-v2

Run research weekly (every Monday) or on-demand before major build decisions. Use the `task` tool with `subagent_type: general` to execute.

## Research Topics

### 1. Biometric Verification (InsightFace / MediaPipe)
- New InsightFace releases, model updates (buffalo_l, buffalo_s, antelopev2)
- MediaPipe FaceMesh updates, TensorFlow.js face-landmarks-detection changes
- Browser-based gaze tracking libraries (WebGazer updates, alternatives)
- Server-side face comparison alternatives (AWS Rekognition, Azure Face API pricing changes)
- ONNX runtime updates, CPU inference performance benchmarks

### 2. Crypto Wallet Blockchain APIs
- Free tier limits and rate limiting for:
  - Etherscan (ETH), BscScan (BNB), Solscan (SOL)
  - Blockchain.com (BTC), chainz.cryptoid.info (LTC)
  - data.ripple.com (XRP)
- Paid plan pricing at scale (100k+ wallets)
- Alternative APIs (Moralis, Alchemy, QuickNode — pricing comparison)
- WalletConnect / MetaMask SDK updates

### 3. Google OAuth & Social Login
- Google Identity Services (GIS) updates, breaking changes
- OAuth consent screen requirements, verification process
- Authorized JavaScript origins best practices for multi-domain SPAs
- Apple Sign-In setup requirements
- Facebook/WhatsApp login options

### 4. CloudFront SPA Deployment
- S3 + CloudFront SPA routing patterns (custom error responses vs. Lambda@Edge)
- Cache invalidation strategies for frequent frontend updates
- CloudFront pricing (data transfer, request costs)
- Alternative CDN costs (Cloudflare, Fastly)

### 5. Docker + pnpm Workspace Best Practices
- Multi-stage build patterns for pnpm monorepos
- pnpm deploy vs. node-linker=hoisted for Docker
- ECS Fargate startup optimization (health checks, migration on boot)
- TSX vs compiled JavaScript in production containers

### 6. SA Fintech & Crypto Regulations
- Crypto asset service provider licensing (FSCA) requirements
- POPIA guidance on biometric data (face embeddings, consent requirements)
- Cross-border payment regulations for marketplace platforms
- Payment gateway options for SA (Yoco, PayFast, Peach Payments, Stripe)

### 7. React Native & Mobile
- React Native biometric libraries (face detection, camera access)
- Background geolocation in React Native (iOS/Android)
- Push notification services (FCM vs OneSignal pricing)
- Expo vs bare React Native for MVP

### 8. Competitor Landscape (Attention Marketplaces)
- Swagbucks, InboxDollars, PrizeRebel — payout models, traffic
- UserTesting, Respondent.io — paid feedback platforms
- Google Ads / Facebook Ads — cost per verified view benchmarks
- Any new attention marketplace entrants
- UBI/crypto-based attention platforms

## Output Format
Append findings to `research/findings.md` with date header and notes per topic. Include source URLs where applicable.
