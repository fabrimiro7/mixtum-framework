
import { Injectable } from '@angular/core';

@Injectable()
export class DateParser {


    ISOToNormalDate(djangoDateFormat: any)
    {   
        if(djangoDateFormat != null){
        var step0 = djangoDateFormat.split('T');
        var step1 = step0[0].split('-',3);
        var year = step1[0];
        var month = step1[1];
        var day = step1[2];
        var hours = step0[1].substring(0, 5);
        var res = day + "/" + month + "/" + year + " (" + hours + ")";
        return res;
        }
        else return null;
    } 

    ISOToNormalDateNoTime(djangoDateFormat: any)
    {
        if(djangoDateFormat != null){
            var step0 = djangoDateFormat.split('T');
            var step1 = step0[0].split('-',3);
            var year = step1[0];
            var month = step1[1];
            var day = step1[2];
            var res = day + "/" + month + "/" + year;
            return res;
            }
            else return null;
        
    }
    
    dateTimeLocalConverter (djangoDateFormat: any) {
        if(djangoDateFormat != null){
            var step0 = djangoDateFormat.split('Z');
            return step0[0];

        }

        else return null;
    }
}