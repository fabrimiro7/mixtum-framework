import { Component, Input, OnInit } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { Observable } from 'rxjs';
import { ImageCropperComponent } from './components/image-cropper/image-cropper.component';
import { AuthService } from 'src/app/services/auth/auth.service';

@Component({
  selector: 'app-avatar',
  templateUrl: './avatar.component.html',
  styleUrls: ['./avatar.component.scss'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      multi: true,
      useExisting: AvatarComponent
    }
  ]
})
export class AvatarComponent implements OnInit, ControlValueAccessor {

  @Input() idUser: any;
  @Input() avatarUrl!: string;

  file: string = '';

  constructor(
    public dialog: MatDialog,
    private profileService: AuthService,
  ) {}

  ngOnInit(): void {
    this.loadUserAvatar();
  }

  writeValue(_file: string): void {
    this.file = _file;
  }
  registerOnChange(fn: any): void {
    this.onChange = fn;
  }
  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }
  setDisabledState?(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  onChange = (file: any) => {
    this.profileService.editAvatarUser(this.idUser, file)
      .subscribe((data: any) => {
        console.log("success");
      })
  };

  onTouched = () => {};

  disabled: boolean = false;

  onFileChange(event: any) {
    const files = event.target.files as FileList;
    
    if (files.length > 0) {
      const filename = files[0].name
      const _file = URL.createObjectURL(files[0]);
      this.resetInput();
      this.openAvatarEditor(_file)
      .subscribe(
        (result) => {
          if(result){

            this.file = result;
            // Convert base64 to Blob
            const byteString = atob(result.split(',')[1]);
            const mimeString = result.split(',')[0].split(':')[1].split(';')[0];
            const ab = new ArrayBuffer(byteString.length);
            const ia = new Uint8Array(ab);
            for (let i = 0; i < byteString.length; i++) {
              ia[i] = byteString.charCodeAt(i);
            }
            const blob = new Blob([ab], { type: mimeString });

            const formData = new FormData();
            formData.append('avatar', blob, filename);
            this.onChange(formData);
          }
        }
      )
    }
  }

  openAvatarEditor(image: string): Observable<any> {
    const dialogRef = this.dialog.open(ImageCropperComponent, {
      maxWidth: '80vw',
      maxHeight: '80vh',
      data: image,
    });

    return dialogRef.afterClosed();
  }

  resetInput(){
    const input = document.getElementById('avatar-input-file') as HTMLInputElement;
    if(input){
      input.value = "";
    }
  }

  loadUserAvatar(): void {
    if (this.avatarUrl && this.avatarUrl != '')
      this.file = this.avatarUrl;
  }

}
