<template>
  <n-layout style="min-height: 100vh;">
    <n-layout-content style="padding: 0;">
      <div style="display: flex; min-height: 100vh;">
        <!-- Left: Colored Background - 60% -->
        <div style="width: 60%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center;">
          <div style="text-align: center; color: white; padding: 48px;">
            <n-h1 style="color: white; font-size: 3rem; margin-bottom: 16px;">Welcome</n-h1>
            <n-text style="font-size: 1.2rem; color: rgba(255, 255, 255, 0.9);">
              Create your account to start exploring our image search platform
            </n-text>
          </div>
        </div>

        <!-- Right: Register Form - 40% -->
        <div style="width: 40%; display: flex; align-items: center; justify-content: center; padding: 24px; background: white; min-height: 100vh;">
          <n-card style="width: 100%; max-width: 400px; padding: 24px;" :bordered="false" embedded>
            <n-h2 style="text-align: center; margin-bottom: 32px; color: #333;">Register</n-h2>

            <n-form @submit.prevent="register" ref="formRef" :model="formModel" :rules="rules">
              <n-form-item path="name" label="Name">
                <n-input v-model:value="formModel.name" placeholder="Enter your name" />
              </n-form-item>

              <n-form-item path="email" label="Email">
                <n-input v-model:value="formModel.email" placeholder="Enter your email" type="email" />
              </n-form-item>

              <n-form-item path="password" label="Password">
                <n-input v-model:value="formModel.password" placeholder="Enter your password (min 8 characters)" type="password" show-password-on="mousedown" />
              </n-form-item>

              <n-form-item path="confirmPassword" label="Confirm Password">
                <n-input v-model:value="formModel.confirmPassword" placeholder="Confirm your password" type="password" show-password-on="mousedown" />
              </n-form-item>

              <n-alert v-if="errorMessage" type="error" style="margin-bottom: 16px;">
                {{ errorMessage }}
              </n-alert>

              <n-button
                type="primary"
                block
                size="large"
                :loading="loading"
                attr-type="submit"
              >
                Register
              </n-button>
            </n-form>

            <n-divider style="margin: 24px 0;" />

            <n-text style="text-align: center; display: block;">
              Already have an account?
              <router-link to="/login">
                <n-button text type="primary">Login Here</n-button>
              </router-link>
            </n-text>
          </n-card>
        </div>
      </div>
    </n-layout-content>
  </n-layout>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useMessage } from 'naive-ui';
import { useAuthStore } from '../stores/authStore';

const router = useRouter();
const authStore = useAuthStore();
const message = useMessage();

const formRef = ref(null);
const errorMessage = ref('');
const loading = ref(false);

const formModel = reactive({
  name: '',
  email: '',
  password: '',
  confirmPassword: ''
});

const rules = {
  name: [
    {
      required: true,
      message: 'Please input your name',
      trigger: 'blur'
    },
    {
      min: 2,
      max: 100,
      message: 'Name must be between 2 and 100 characters',
      trigger: 'blur'
    }
  ],
  email: [
    {
      required: true,
      message: 'Please input your email',
      trigger: ['input', 'blur']
    },
    {
      type: 'email',
      message: 'Please input a valid email',
      trigger: ['blur']
    },
    {
      max: 120,
      message: 'Email must be less than 120 characters',
      trigger: 'blur'
    }
  ],
  password: [
    {
      required: true,
      message: 'Please input your password',
      trigger: ['input', 'blur']
    },
    {
      min: 8,
      max: 128,
      message: 'Password must be between 8 and 128 characters',
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    {
      required: true,
      message: 'Please input your password again',
      trigger: ['input', 'blur']
    },
    {
      validator: (rule, value) => {
        return formModel.password === value;
      },
      message: 'Password is inconsistent with reconfirmation',
      trigger: ['blur', 'password-input']
    }
  ]
};

const register = async () => {
  try {
    await formRef.value?.validate();

    loading.value = true;
    errorMessage.value = '';

    if (formModel.password !== formModel.confirmPassword) {
      errorMessage.value = 'Passwords do not match';
      loading.value = false;
      return;
    }

    await authStore.register({
      name: formModel.name,
      email: formModel.email,
      password: formModel.password
    });

    loading.value = false;

    // Show success message and redirect to login
    message.success('Registration successful! Please log in to continue.')
    router.push('/login');
  } catch (error) {
    loading.value = false;
    errorMessage.value = error.message || 'Registration failed';
    console.error('Registration error:', error);
  }
};
</script>
