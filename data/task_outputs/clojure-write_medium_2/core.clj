(ns metabase.auth.core
  "User authentication and session management namespace.
   Provides functions for secure password handling, validation, and session control."
  (:require
    [buddy.core.hash :as hash]
    [buddy.core.codecs :as codecs]
    [buddy.hashers :as hashers]
    [clojure.spec.alpha :as s]
    [clojure.spec.alpha :as spec]
    [ring.middleware.session :as session]))

;; Specs for validating user inputs
(s/def ::username (s/and string? #(re-matches #"[a-zA-Z0-9_]{3,20}" %)))
(s/def ::password (s/and string? #(>= (count %) 8)))

(defn hash-password
  "Securely hash a user's password using bcrypt."
  [password]
  {:pre [(s/valid? ::password password)]}
  (hashers/derive password {:alg :bcrypt+sha512}))

(defn verify-password
  "Verify a password against a stored hash."
  [plain-password hashed-password]
  {:pre [(s/valid? ::password plain-password)]}
  (hashers/verify plain-password hashed-password))

(defn create-user
  "Create a new user with a securely hashed password."
  [username password]
  {:pre [(s/valid? ::username username)
         (s/valid? ::password password)]}
  {:username username
   :password (hash-password password)})

(defn generate-session-token
  "Generate a secure session token."
  []
  (codecs/bytes->hex (hash/sha256 (str (System/currentTimeMillis)))))

(defn create-session
  "Create a new user session with a unique token."
  [user-id]
  {:session-token (generate-session-token)
   :user-id user-id
   :created-at (System/currentTimeMillis)})

(defn validate-session
  "Check if a session is valid based on token and timeout."
  [session max-age-ms]
  (let [current-time (System/currentTimeMillis)]
    (and session
         (< (- current-time (:created-at session))
            max-age-ms))))

(defn invalidate-session
  "Invalidate a user session."
  [session]
  (assoc session :invalidated-at (System/currentTimeMillis)))
