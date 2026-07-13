    <template>
        <div>
            <h1>403 - Access Denied</h1>
            <p>You do not have permission to access this resource.</p>
        </div>
    </template>
    <script>
    import router from '@/router'
    import { sleep } from '@/services/sleep'
    export default {
        name: 'Error403'
    }
    sleep(2000).then(() => {
        router.push({ name: 'Dashboard' })
    })
    </script>
    <style scoped>
    h1 {
        color: red;
    }
    p {
        font-size: 18px;
        display: inline-block;
        display: block;
    }
    </style>