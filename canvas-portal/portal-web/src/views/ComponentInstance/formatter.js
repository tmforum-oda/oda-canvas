export const formatStatus = value => {
    let color;
    switch (value) {
        case 'In Progress':
            color = '#5bc0de';
            break;
        case 'Failed':
            color = '#e74c3c';
            break;
        case 'Complete':
            color = '#5cb85c';
            break;
        default:
            color = '#777';
            break;
    }
    return `<span style="color: ${color}"><span style="margin-right: 5px;display: inline-block;width: 9px;height: 9px;background: ${color};border-radius: 50%;"></span>${value}</span>`;
}
export const formatDomain = domain => {
    if (!domain) return '';
    let color;
    switch (domain) {
        case 'Party':
            color = '#9E3535';
            break;
        case 'Intelligence':
            color = '#5DCB79';
            break;
        case 'Production':
            color = '#227CF9';
            break;
        case 'Core Commerce Management':
            color = '#0BCDA7';
            break;
        default:
            color = '#777';
            break;
    }
    return `<span class="label" style="font-size:12px;background-color: ${color};display:inline;padding:2px 6px 3px;font-weight:700;line-height:1;color:#fff;text-align:center;white-space:nowrap;vertical-align:middle;border-radius:.25em;font-family: Helvetica Neue,Helvetica,PingFang SC,Hiragino Sans GB,Microsoft YaHei,\\\\5FAE\\8F6F\\96C5\\9ED1,Arial,sans-serif;">${domain}</span>`;
}

export const dealApiStatus = status => {
    let text;
    let color;
    if (status === true) {
        text = 'Ready';
        color = '#5cb85c';
    } else {
        text = 'NotReady';
        color = '#f0ad4e';
    }
    return `<span class="label font-custom" style="color: ${color};border: 1px solid ${color};display: inline;padding: 0.2em 0.6em 0.3em;font-size: 75%;font-weight: 700;line-height: 1;text-align: center;white-space: nowrap;vertical-align: baseline;border-radius: 0.25em;">${text}</span>`;
}

export default {
    formatStatus,
    formatDomain,
    dealApiStatus
};