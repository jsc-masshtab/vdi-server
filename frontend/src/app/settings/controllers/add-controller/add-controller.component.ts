import { WaitService } from './../../../common/components/wait/wait.service';
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


  constructor(private service: ControllersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddControllerComponent>) {}


  public send() {
    this.waitService.setWait(true);
    this.service.addController(this.controller,this.description).subscribe((res) => {
      this.service.getAllControllers().valueChanges.subscribe();
      this.dialogRef.close();
      this.waitService.setWait(false);
    },(error)=> {
    
    });

  
  }

}
