async function trackActivity(activityType, minutesSpent = 1, topicSlug = null) {
    if (typeof authFetch !== "function" || !getAccessToken()) return;

    try {
        await authFetch("/activity/log", {
            method: "POST",
            body: {
                activity_type: activityType,
                minutes_spent: minutesSpent,
                topic_slug: topicSlug
            }
        });
    } catch (err) {
        console.warn("Activity tracking failed:", err);
    }
}
