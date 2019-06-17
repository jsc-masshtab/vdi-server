import { MatDialogRef } from '@angular/material';
import { Component } from '@angular/core';
import { ControllersService } from '../controllers.service';


@Component({
  selector: 'vdi-add-controller',
  templateUrl: './add-controller.component.html'
})

export class AddControllerComponent {

  public controller: string = "";
  public description: string = "";
  public validate:boolean = false;


  constructor(private service: ControllersService,
              private dialogRef: MatDialogRef<AddControllerComponent>) {}


  public send() {
    // if(!this.controller || !this.description) {
    //   this.validate = true;
    //   return;
    // }
    this.validate = false;
    this.service.addController(this.controller,this.description).subscribe((res) => {
      if(res) {
        this.service.getAllControllers().valueChanges.subscribe();
        this.dialogRef.close();
      }
    },(error)=> {
    });
  }

}
