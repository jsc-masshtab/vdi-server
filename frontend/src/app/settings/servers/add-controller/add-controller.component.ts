import { MatDialogRef } from '@angular/material';
import { Component, OnInit } from '@angular/core';
import { ServersService } from './../servers.service';


@Component({
  selector: 'vdi-add-controller',
  templateUrl: './add-controller.component.html'
})

export class AddControllerComponent {

  public controller: string;
  public description: string;


  constructor(private service: ServersService,
              private dialogRef: MatDialogRef<AddControllerComponent>) {}


  public send() {
    this.service.addController(this.controller,this.description).subscribe((res) => {
      if(res) {
        this.service.getAllControllers().valueChanges.subscribe();
        this.dialogRef.close();
      }
    },(error)=> {

    });
  }

}
