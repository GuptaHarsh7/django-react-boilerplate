import axios from 'axios';
import {APIEndpoint} from '../constants'

export const updateObject = (oldObject, updatedProperties) => {
  return {
    ...oldObject,
    ...updatedProperties
  };
};

export const authAxios = axios.create({
  baseURL: APIEndpoint,
  headers : {
    Authorization: {
      toString(){
        return `Token ${localStorage.getItem('token')}`;
      }
    }
  }
});