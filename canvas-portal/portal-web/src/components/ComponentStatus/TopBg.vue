<template>
    <div class="oda-bg-container">
        <div class="top-gb-title">
            Open Digital Architecture
        </div>
        <div class="top-gb-parg">ODA transforms business agility, customer
            experience and operational efficiency</div>
        <div class="top-gb-parg">by creating simpler IT solutions that are easier
            and cheaper to deploy, integrate &</div>
        <div class="top-gb-parg">upgrade.</div>
    </div>
</template>

<style lang="scss" scoped>
.oda-bg-container {
    height: 230px;
    width: 100%;
    background: url('@/assets/images/oda-background.png');
    background-size: cover;
    background-repeat: no-repeat;
    padding: 40px 80px;

    .top-gb-title {
        font-family: FZLTCHJW--GB1-0;
        font-size: 44px;
        color: #FFFFFF;
        font-weight: bold;
        background-image: -webkit-linear-gradient(#fff, #fff, #4A70CB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }

    .top-gb-parg {
        font-size: 16px;
        color: #CDD8F1;
        font-weight: 400;
    }
}
</style>