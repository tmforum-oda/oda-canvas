import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
dayjs.extend(relativeTime);

export const formatDate = (timestamp, format = 'YYYY-MM-DD HH:mm:ss') => {
    return dayjs(timestamp).format(format);
}
