import tkinter as tk
from tkinter import ttk, messagebox
import requests
import os
import sys
import webbrowser
from tqdm import tqdm
from threading import Thread

class MovieDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Torrent Downloader")
        self.root.geometry("800x600")
        
        # Search Frame
        search_frame = ttk.Frame(root, padding="10")
        search_frame.pack(fill=tk.X)
        
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Search", command=self.search_movies).pack(side=tk.LEFT)
        
        # Results Frame
        results_frame = ttk.Frame(root, padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Movie List
        columns = ('title', 'year', 'rating', 'qualities')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings')
        
        self.tree.heading('title', text='Title')
        self.tree.heading('year', text='Year')
        self.tree.heading('rating', text='Rating')
        self.tree.heading('qualities', text='Available Qualities')
        
        self.tree.column('title', width=300)
        self.tree.column('year', width=70)
        self.tree.column('rating', width=70)
        self.tree.column('qualities', width=200)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Download Button
        ttk.Button(root, text="Download Selected", command=self.download_selected).pack(pady=10)
        
        # Progress Bar
        self.progress = ttk.Progressbar(root, length=300, mode='determinate')
        self.progress.pack(pady=10)
        
        self.movies_data = []

    def search_movies(self):
        movie_name = self.search_var.get()
        if not movie_name:
            messagebox.showwarning("Warning", "Please enter a movie name")
            return
            
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        base_url = "https://yts.mx/api/v2/list_movies.json"
        params = {"query_term": movie_name}
        
        try:
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data["data"]["movie_count"] > 0:
                    self.movies_data = data["data"]["movies"]
                    for movie in self.movies_data:
                        qualities = ", ".join([t['quality'] for t in movie['torrents']])
                        self.tree.insert('', tk.END, values=(
                            movie['title'],
                            movie['year'],
                            movie['rating'],
                            qualities
                        ))
                else:
                    messagebox.showinfo("Info", "No movies found!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def download_movie(self, url, filename):
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', -1))
    
        if total_size == -1:
            self.progress.config(mode='indeterminate')
            self.progress.start()
        else:
            self.progress.config(mode='determinate')
            self.progress['maximum'] = total_size
    
        try:
            with open(filename, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        if total_size != -1:
                            downloaded += len(chunk)
                            self.progress['value'] = downloaded
                            self.root.update_idletasks()
        
            self.progress.stop()
            self.progress['value'] = 0
        
            # Use os.system to open the torrent file with system default application
            if sys.platform.startswith('linux'):
                os.system(f'xdg-open "{filename}"')
            elif sys.platform.startswith('darwin'):
                os.system(f'open "{filename}"')
            elif sys.platform.startswith('win32'):
                os.system(f'start "" "{filename}"')
        
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {str(e)}")
            return   
         
    def download_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a movie")
            return
            
        selected_index = self.tree.index(selected_item)
        selected_movie = self.movies_data[selected_index]
        
        # Create quality selection window
        quality_window = tk.Toplevel(self.root)
        quality_window.title("Select Quality")
        quality_window.geometry("300x200")
        
        qualities = selected_movie['torrents']
        quality_var = tk.StringVar()
        
        for i, q in enumerate(qualities):
            ttk.Radiobutton(
                quality_window,
                text=f"{q['quality']} ({q['size']})",
                value=i,
                variable=quality_var
            ).pack(pady=5)
            
        def start_download():
            quality_index = int(quality_var.get())
            selected_quality = qualities[quality_index]
            
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
                
            filename = f"downloads/{selected_movie['title']}_{selected_quality['quality']}.torrent"
            
            quality_window.destroy()
            
            # Start download in a separate thread
            Thread(
                target=self.download_movie,
                args=(selected_quality['url'], filename)
            ).start()
            
        ttk.Button(quality_window, text="Download", command=start_download).pack(pady=10)

def main():
    root = tk.Tk()
    app = MovieDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
