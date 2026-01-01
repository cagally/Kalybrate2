(ns metabase.websocket.handler
  (:require [clojure.core.async :as async]
            [taoensso.sente :as sente]
            [taoensso.sente.server :as sente-server]
            [taoensso.sente.channels :as channels]))

(defonce channels (atom {}))

(defmulti -event-msg-handler
  "Multimethod to handle different types of WebSocket events"
  :id)

(defmethod -event-msg-handler :default
  [{:keys [event] :as msg}]
  (println "Unhandled event:" event))

(defmethod -event-msg-handler :chsk/recv
  [{:keys [event] :as msg}]
  (let [[_ payload] event]
    (println "Received payload:" payload)))

(defmethod -event-msg-handler :chsk/handshake
  [{:keys [event] :as msg}]
  (println "WebSocket handshake completed"))

(defn start-websocket-router! [ch-chsk]
  (let [stop-fn (sente-server/start-chsk-router! ch-chsk -event-msg-handler)]
    stop-fn))

(defn send-client-msg! [uid event]
  (when-let [channel (get @channels uid)]
    (channels/chsk-send! channel event)))

(defn broadcast-msg! [event]
  (doseq [uid (keys @channels)]
    (send-client-msg! uid event)))
