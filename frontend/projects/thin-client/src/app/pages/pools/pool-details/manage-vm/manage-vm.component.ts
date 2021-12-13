import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'app-manage-vm',
  templateUrl: './manage-vm.component.html',
  styleUrls: ['./manage-vm.component.scss']
})
export class ManageVmComponent{
  @Output()
  public readonly manageVM = new EventEmitter<string>();
  @Output()
  public readonly openDialog = new EventEmitter<void>();

  public onClickAction(action: string): void{
    this.manageVM.emit(action)
  }

  public onClickOpenDialog(): void {
    this.openDialog.emit()
  }

}
